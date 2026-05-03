%include "examples/roman_numerals/macros/number_to_roman.sas";

libname rdemo "examples/roman_numerals/testdata";

data work.SASPYTEST_ROMAN_INPUT;
    set rdemo.saspytest_roman_input;
run;

data work.SASPYTEST_ROMAN_OUTPUT;
    set work.SASPYTEST_ROMAN_INPUT;
    length roman $16;

    roman = resolve(
        cats(
            '%number_to_roman(',
            strip(put(number, best.-l)),
            ')'
        )
    );
run;

%let SASPYTEST_ROMAN_STATUS = COMPLETE;

%put NOTE: Roman numeral conversion demo completed.;
