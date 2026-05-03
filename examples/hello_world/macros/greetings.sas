/*------------------------------------------------------------------
Macro: greetings
Purpose: Write an informational greeting to the SAS log.
Parameters:
    name - Name of the person to greet (required)
------------------------------------------------------------------*/
%macro greetings(name);
    %if %superq(name) = %then %do;
        %put %str(WAR)NING: No name provided to GREETINGS macro.;
        %let syscc = %sysfunc(max(&syscc, 4));
        %return;
    %end;

    %put NOTE: Invoking greetings macro for &name.;
    %put Hello, &name.%str(!);
%mend greetings;
