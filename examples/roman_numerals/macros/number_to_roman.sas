%macro number_to_roman(value);
    %local _value _roman;

    %if %superq(value) = %then %do;
        %put %STR(ERR)OR: number_to_roman requires an integer input between 1 and 999.;
        %let syscc = %sysfunc(max(&syscc, 8));
        %return;
    %end;

    %if %sysfunc(notdigit(%superq(value))) > 0 %then %do;
        %put %STR(ERR)OR: number_to_roman requires an integer input between 1 and 999.;
        %let syscc = %sysfunc(max(&syscc, 8));
        %return;
    %end;

    %let _value = %sysfunc(inputn(%superq(value), best.));

    %if &_value < 1 or &_value > 999 %then %do;
        %put %STR(ERR)OR: number_to_roman only supports values between 1 and 999.;
        %let syscc = %sysfunc(max(&syscc, 8));
        %return;
    %end;

    %let _roman = %str();

    %do %while(&_value >= 900);
        %let _roman = &_roman.CM;
        %let _value = %eval(&_value - 900);
    %end;
    %do %while(&_value >= 500);
        %let _roman = &_roman.D;
        %let _value = %eval(&_value - 500);
    %end;
    %do %while(&_value >= 400);
        %let _roman = &_roman.CD;
        %let _value = %eval(&_value - 400);
    %end;
    %do %while(&_value >= 100);
        %let _roman = &_roman.C;
        %let _value = %eval(&_value - 100);
    %end;
    %do %while(&_value >= 90);
        %let _roman = &_roman.XC;
        %let _value = %eval(&_value - 90);
    %end;
    %do %while(&_value >= 50);
        %let _roman = &_roman.L;
        %let _value = %eval(&_value - 50);
    %end;
    %do %while(&_value >= 40);
        %let _roman = &_roman.XL;
        %let _value = %eval(&_value - 40);
    %end;
    %do %while(&_value >= 10);
        %let _roman = &_roman.X;
        %let _value = %eval(&_value - 10);
    %end;
    %do %while(&_value >= 9);
        %let _roman = &_roman.IX;
        %let _value = %eval(&_value - 9);
    %end;
    %do %while(&_value >= 5);
        %let _roman = &_roman.V;
        %let _value = %eval(&_value - 5);
    %end;
    %do %while(&_value >= 4);
        %let _roman = &_roman.IV;
        %let _value = %eval(&_value - 4);
    %end;
    %do %while(&_value >= 1);
        %let _roman = &_roman.I;
        %let _value = %eval(&_value - 1);
    %end;

    &_roman

%mend number_to_roman;
