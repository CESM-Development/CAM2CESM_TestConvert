# General note on CESM tests

Each test for CESM is defined by a combination of several factors:

1. General test type/script, e.g. SMS, ERI, ...
2. Test modifiers, e.g. _D for debug, _Ld3 for 3 days...
3. Compset (A, B1850WCN, FAMIPC5,...)
4. Resolution (f19\_g16, ne30\_ne30, ...)
5. The new testmods options, e.g. clm-default

(You also have to specify machine and compiler to actually run, but this is not
part of the model configuration and really orthogonal to anything that we would
have to translate.)

So the goal is roughly to translate each CAM tests into an appropriate
combination of these five settings. The most difficult part will probably be
translation of the options to configure (the files in
`$CESMROOT/models/atm/cam/test/system/config_files`), because these overlap with
all five of the pieces that define the CESM test.

# input_tests_master format

Input_tests are specified using 3-7 columns. The most common order, e.g. for
smoke and restart tests, is as follows:

| Column      | 1        | 2         | 3            | 4           | 5          |
|-------------|----------|-----------|--------------|-------------|------------|
| Name        | Test id  | Script    | config\_file | nl\_file    | Run length |
| CESM analog | N/A      | Test type | Various      | user\_nl\_* | _L*        |

For TEQ and TSC tests, there are two runs involved. In that case, columns 5 and
6 are the config and nl files for the second run, and column 7 is the run
length.

Note that all cases are F cases (no active ocean, prescribed sea ice), and all
currently use CLM 4.0 with generic settings, so the only meaningful
configuration in most cases is for CAM itself.

# Scripts translation

## Tests that run cases

Here's a quick and dirty comparison of CAM vs. CESM test scripts that involve
an actual run setup.

CAM script | CESM script | Purpose
-----------|-------------|--------
TCB        | N/A         | Configure and build test
TSM        | SMS         | Smoke test
TER        | ERT         | Exact restart test
TBR        | ERB*        | Exact branch test
TBL        | N/A         | History file comparison against baseline
TPF        | N/A         | Throughput comparison against baseline
TEQ        | N/A         | Test equal configurations
TNE        | N/A         | Test unequal configurations
TSC        | N/A         | SCAM generated IOP test

We never really run TCB tests anymore, because if we bother building a case we
usually go ahead and run it for a few timesteps as a smoke test. In any case,
TCB, TBL, and TPF tests do not really need to be translated. It appears that,
with the CESM scripts, if you run a test case with a baseline to compare to, the
scripts will compare answers and look for performance regressions automatically.

TSM, TER, and TBR tests all translate directly into a CESM equivalent, with one
possible exception. It seems that an ERB test checks for exact restart, but does
not actually check to see that a branch is exact. If that is correct, ERB tests
will need a minor modification to check for exact branching. This translation
also depends upon the CESM scripts checking atm history files.

It should be pointed out that a lot of CAM test lists involve running TSM, TER,
and TBL, or TSM, TER, TBL, and TBR. With the CESM tests, it should be possible
to run a single ERT (ERS?) or ERB test to cover the exact same cases.

Most of the above list can therefore be translated with scripts that already
exist. The three exceptions are TEQ, TNE, and TSC.

TEQ/TNE tests are a long-desired feature in the CESM scripts, specifically to
verify that two configurations are (or are not) the same. If they are
implemented soon, we should be able to do this translation. Currently, CAM only
compares cases that use the same executable with different run-time options. It
would be easier to implement this in CESM than to implement full equality
checking (with different executables), but in the long run both would be
helpful.

It's not clear how TSC should be translated. A TSC test generates an IOP file
for SCAM (which currently can only be done by the Eulerian dycore), and then
runs a SCAM test that uses that file. As far as I know, there are not currently
any CESM tests that run one configuration, then use the output file as an input
to a totally separate configuration. This seems to require dependent jobs.

## Tests that parse text

There are a few CAM-specific tests that just look at text output:

CAM script | Purpose
-----------|--------
TDD        | Test divergence damping option
TMC        | Mass conservation check
TFM        | Subversion mergeinfo
TR8        | Require explicit precision on floating-point literals

The TDD test seems to have been a one-off test that build-namelist works. It's
not useful and should just be thrown out.

TMC looks through the CAM log for messages about a test tracer, and prints an
error when "mass" of this fictional tracer is not conserved. This is only valid
in runs with (at least?) five test tracers requested via configure options. This
test never fails, so it's not so clear what it's actually doing; Brian Eaton
should know.

TFM checks for bad Subversion mergeinfo. It may be relevant to other CESM
components that want to police this sort of thing, but not relevant to Git-based
projects.

TR8 enforces a CAM coding standard where all floating-point literals must have
an explicitly specified precision. It parses Fortran files in order to search
for violations. It should accept `1.0_r8` and `1.0D0`, but reject `1.0` and
`1.0E0`. Comments and string literals are filtered out to avoid false positives.

TR8 is probably of general interest. It relies, however, on Ruby code created by
Tom Henderson at NOAA, which is not distributed with CESM.

## *_ccsm tests

The "_ccsm" tests (e.g. TSM\_ccsm.sh) are only used to compare CAM standalone to
CESM tests, to reduce the chance of the CAM test suite passing on a CAM tag that
later causes problems for CESM. This means that it's inherently pointless to
literally translate these tests to the CESM test suite.

However, the CESM scripts could probably use a bit more testing to avoid cases
where, for instance, create\_test cases work but create\_newcase cases do not,
or where cases run successfully but the short-term archiver is broken.

# config_file translation

To be continued! A preview of what we need to resolve:

## Options corresponding to test options (e.g. -debug)

## Options corresponding to the grid (-dyn, -res)

## Options corresponding to the compset (e.g. -phys)

## Options corresponding to testmods (e.g. -cosp)
