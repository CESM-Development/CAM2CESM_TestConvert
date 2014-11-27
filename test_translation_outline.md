# General note on CESM tests

Each test for CESM is defined by a combination of several factors:

1. General test type/script, e.g. SMS, ERI, ...
2. Test options included in the name, e.g. \_D for debug, \_Ld3 for 3 days...
3. Compset (A, B1850WCN, FAMIPC5,...)
4. Resolution (f19\_g16, ne30\_ne30, ...)
5. The new(-ish) testmods options, e.g. clm-default

(You also have to specify machine and compiler to actually run, but this is not
part of the model configuration and really orthogonal to anything that we would
have to translate.)

So the goal is roughly to translate each CAM tests into an appropriate
combination of these five settings. The most difficult part will probably be
translation of the options to configure (the files in
`$CESMROOT/models/atm/cam/test/system/config_files`), because these overlap with
all five of the pieces that define the CESM test.

# input_tests_master format

Input tests are specified using 3-7 columns. The most common order, e.g. for
smoke and restart tests, is as follows:

| Column      | 1        | 2         | 3            | 4                     | 5          |
|-------------|----------|-----------|--------------|-----------------------|------------|
| Name        | Test id  | Script    | config\_file | nl\_file + use\_case  | Run length |
| CESM analog | N/A      | Test type | Various      | user\_nl\_* + compset | \_L*       |

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
TER        | PRS         | Exact restart test
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

TSM, TER, and TBR tests all translate directly into a CESM equivalent, aside
from one issue with TBR tests. Note that TER seems to be most similar to a "PRS"
test rather than an ERS or ERT test, because it actually changes the number of
tasks and threads before restarting. However, a PRS test will be a bit slower
because it rebuilds when changing the task number (which is technically a
requirement of CICE), whereas standalone CAM hacks around this to reuse the
same executable with different layouts.

The one difference between TBR and ERB is that an ERB test checks for exact
restart, but does not seem to actually check to see that a branch is exact. If
that is correct, ERB tests will need a minor modification to check for exact
branching. This translation also depends upon the CESM scripts checking atm
history files.

It should be pointed out that a lot of CAM test lists involve running TSM, TER,
and TBL, or TSM, TER, TBL, and TBR. With the CESM tests, it should be possible
to cover the exact same cases with only one or two tests each.

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
test does not have a tolerance specified, so it is extremely strict. It is only
run with the Eulerian dycore, and would probably fail with FV or SE. We may need
to talk to Brian Eaton about what exactly is covered, and whether it's worth
keeping (perhaps in some modified form) moving forward.

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

## Options that we can ignore

- `-s`: This "silent mode" is automatically added by CESM. It does not turn off
  the reporting of errors, so this does not usually interfere with debugging of
  failed tests.

- `-ice`/`-lnd`: Ice and land components. CAM only defines these to maintain
  consistency with its own configuration and whatever ocean has been chosen. The
  CESM compsets are already consistent, so we don't have to translate these
  options.

## Options corresponding to test name options (or `-confopts` to create_newcase)

- `-debug`: Corresponds to the `_D` option in the CESM test name. This changes
  compile-time options and also turns on some asserts at run-time.

- `-spmd`/`-nospmd`: Turns MPI on or off. `-nospmd` should be equivalent to the
  `_Mmpi-serial` option in CESM, but is probably only used for SCAM cases.

## Options corresponding to the grid

- `hgrid`/`-res`: Translates directly into the atm/lnd part of the CESM test's
  grid, so this should be easy. These two options are synonyms (`-res` is
  deprecated).

  The one exception would be Eulerian/SLD grids, which have names that don't
  match up with their CESM counterparts. (E.g. CAM's 48x96 is CESM's T31.) The
  translation can be looked up in
  `scripts/ccsm_utils/Case.template/config_grid.xml`. We may need to add grids
  to that file and to `config_compsets.xml`, using the information in
  `$CAMROOT/bld/config_files/horiz_grid.xml` and
  `$CAMROOT/bld/namelist_files/namelist_defaults_cam.xml`.

- `-dyn`: Specifies the dycore. Currently we can ignore this, except for any
  `-dyn sld` tests, which will need testmods for this option as long as we
  continue to support the dycore. This is because the SLD and Eulerian dycores
  are the only two dycores that can run on the same grids.

  The SLD dycore may be removed from CAM at some point before CESM 2, and is not
  used by ACME. However, we may want to retain the `-dyn` option as a separate
  (optional?)  argument to configure, because new dycores in the future may run
  on the same grids as each other or as CAM-SE.

## Options corresponding to the compset and/or testmods

Note that it's better to look at the use\_case first to decide what compset you
are running; in most cases, if the use\_case from a test matches a CESM compset,
the following options will all match as well. But this will have to be
double-checked for each test. If there is no use\_case, it may also still be the
case that there is a compset corresponding to these options, but this is
certain.

For any desired combination in the tests that does not correspond to a compset,
we will have to pick a "close" compset and use testmods to correct the
difference.

- `-phys`: Broad collections of physics packages (e.g. `cam5`, `ideal`, etc.).
  Note that standalone CAM still supports CAM3 physics, but there are no
  compsets for this. (However, there's little to no difference between CAM3 and
  CAM4 builds, so resurrecting a basic CAM3 compset in the scripts should be
  trivial.)

- `-chem`: Chemistry package. The working groups associated with WACCM and CAM-
  CHEM have only supported CESM scripts to their users, so tests that specify
  a chemistry other than `none` or `trop_mam*` should correspond to specific
  compsets in most cases.

- `-age_of_air_trcs`/`-waccm_phys`: Either part of the compset definition or
  added by configure when using certain `-chem` options, so these should be
  easy.

- `-offline_dyn`/`-nlev`: Specified/nudged dynamics (currently only plugged into
  FV, but SE is being added). Mostly of relevance to CAM-CHEM and WACCM, so
  again the CESM compsets should have correct definitions. (`-nlev` can change
  for many reasons, but CAM's `configure` infers the correct value, except for
  specified dynamics and some experimental/custom configurations.)

- `-waccmx`: Enables WACCM-X, always part of the compset definition.

- `-scam`: Enable SCAM. Hopefully easy; CESM has a couple of SCAM compsets
  already.

- `-offline_drv`: Used to enable "offline" runs where only a single part of the
  physics runs prognostically. PORT is the first and currently only offline tool
  provided using this option, and it corresponds to the `P` compsets in CESM.

- `-ocn`: Most standalone CAM tests use the CESM data ocean (docn), but there
  are a few tests that use aquaplanet, and these need to be translated to an
  AQUAP compset.

  CAM also has a legacy data ocean model (dom). We only do minimal testing of
  this, and it's not clear whether/why we need to keep it, since at face value
  docn seems to have superceded it.

- `-clubb_sgs`: Turns on CLUBB. A compset already exists for this case.

- `-carma`: Turns on a CARMA model. The `bc_strat` and `sulfate` models have
  associated compsets. The other cases would need to be added using testmods.

## Options corresponding to testmods

- `-smp`/`-nosmp`: Turns OpenMP on or off. CAM has a pretty even mix of tests
  with and without threading enabled, but CESM does not turn off threading very
  often (except for a few configurations such as I compsets). This means that
  we need to use testmods to force threading off if we want to keep testing
  these configurations without OpenMP.

  For goldbach PGI tests, CAM actually wants the opposite; we need to turn on
  threading on a machine that runs using MPI-only parallelization by default.

- `-nadv_tt`: Adds tracers (used for TMC test).

- `-cppdefs`: The only use of this seems to be to add `-DTRACER_CHECK` to the
  compilation options, which turns on the code used for the TMC test.

- `-pergro`: Enable code used for perturbation growth tests (just to make sure
  that it still runs).

- `-cosp`: COSP diagnostic outputs. Can be added to any compset, but none of
  them enable it by default due to the cost.

- `-microphys`: Change microphysics. Usually implied by the `-phys` option, so
  this is only needed to turn on MG2 until the CAM5.5 or CAM6 compsets are
  defined. (ACME only has MG1.5, but will very likely get MG2 at some point.)

- `-rad`: Only needed to test that RRTMG works with CAM4. (CESM doesn't
  officially support this, but there are some papers based on this combination,
  and it's easy to maintain.)

- `-camiop`: Generates IOP files for later use by SCAM. Needed for translation
  of the TSC tests.

- `-psubcols`: Turns on subcolumns. The infrastructure is complete, but none of
  the schemes that use subcolumns are complete from a scientific perspective, so
  there is no compset. Nonetheless, we test the infrastructure by checking that
  subcolumns that are just copies of the original columns get bit-for-bit
  answers with the non-subcolumnized model.

- `-prog_species`/`-usr_mech_infile`: Custom chemistry mechanisms.
  `-prog_species` will create a custom chemistry mechanism based on the chemical
  species listed on the command line. `-usr_mech_infile` allows one to provide a
  manually created custom mechanism file. If either option is specified, the
  chemistry preprocessor is built and run on the mechanism file, and generates
  Fortran source code that will be compiled to implement the custom chemistry
  scheme.

  While none of the files in `config_files` specify `-usr_mech_infile` directly,
  there is logic in TCB.sh that passes `config_files/testmech` as the custom
  file in one test.
