"""Subprocess tests for the pytest plugin and session fixture lifecycle."""

pytest_plugins = ["pytester"]


def test_plugin_does_not_create_session_for_plain_tests(pytester):
    pytester.makepyfile(test_plain="""
        def test_plain():
            assert True
        """)

    result = pytester.runpytest("-p", "saspytest")

    result.assert_outcomes(passed=1)


def test_plugin_autodiscovery_provides_sas_fixture(pytester):
    pytester.makeconftest("""
        import saspy


        class FakeSAS:
            def submit(self, code):
                return {"LOG": "", "LST": ""}

            def endsas(self):
                pass


        saspy.SASsession = FakeSAS
        """)
    pytester.makepyfile(test_fixture="""
        def test_fixture_is_available(sas_session):
            assert sas_session.__class__.__name__ == "FakeSAS"
        """)

    result = pytester.runpytest()

    result.assert_outcomes(passed=1)


def test_failed_test_still_cleans_shared_session(pytester):
    pytester.makeconftest("""
        from pathlib import Path
        import saspy


        def record(value):
            with Path("calls.log").open("a", encoding="utf-8") as stream:
                stream.write(value + "\\n---\\n")


        class FakeSAS:
            def submit(self, code):
                record(code)
                return {"LOG": "", "LST": ""}

            def endsas(self):
                record("ENDSESSION")


        saspy.SASsession = FakeSAS
        """)
    pytester.makepyfile(test_failure="""
        def test_failure(sas_session):
            sas_session.submit("USER CODE")
            assert False
        """)

    result = pytester.runpytest()

    result.assert_outcomes(failed=1)
    calls = (pytester.path / "calls.log").read_text(encoding="utf-8")
    assert calls.count("SASPYTEST_") >= 2
    assert "USER CODE" in calls
    assert "ENDSESSION" in calls


def test_session_creation_failure_is_reported_as_fixture_error(pytester):
    pytester.makeconftest("""
        import saspy


        def fail_to_create_session(*args, **kwargs):
            raise RuntimeError("cannot connect")


        saspy.SASsession = fail_to_create_session
        """)
    pytester.makepyfile(test_creation="""
        def test_requires_session(sas_session):
            assert sas_session
        """)

    result = pytester.runpytest()

    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*RuntimeError: cannot connect*"])


def test_require_new_session_is_cleaned_without_shared_session(pytester):
    pytester.makeconftest("""
        from pathlib import Path
        import saspy


        def record(value):
            with Path("calls.log").open("a", encoding="utf-8") as stream:
                stream.write(value + "\\n---\\n")


        class FakeSAS:
            def submit(self, code):
                record(code)
                return {"LOG": "", "LST": ""}

            def endsas(self):
                record("ENDSESSION")


        saspy.SASsession = FakeSAS
        """)
    pytester.makepyfile(test_new="""
        def test_new_session(require_new_sas_session):
            require_new_sas_session.submit("NEW SESSION CODE")
        """)

    result = pytester.runpytest()

    result.assert_outcomes(passed=1)
    calls = (pytester.path / "calls.log").read_text(encoding="utf-8")
    assert "NEW SESSION CODE" in calls
    assert "ENDSESSION" in calls


def test_session_teardown_failure_is_reported(pytester):
    pytester.makeconftest("""
        import saspy


        class FakeSAS:
            def submit(self, code):
                return {"LOG": "", "LST": ""}

            def endsas(self):
                raise RuntimeError("teardown failed")


        saspy.SASsession = FakeSAS
        """)
    pytester.makepyfile(test_teardown="""
        def test_teardown(sas_session):
            assert sas_session
        """)

    result = pytester.runpytest()

    result.assert_outcomes(passed=1, errors=1)
    result.stdout.fnmatch_lines(["*RuntimeError: teardown failed*"])
