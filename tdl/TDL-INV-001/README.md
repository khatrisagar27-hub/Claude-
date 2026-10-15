# TDL-INV-001: IRN-protected Sales voucher

| | |
|---|---|
| Platform | TallyPrime Edit Log, Release 7.1 |
| Priority | Critical |
| Objective | Stop an existing Sales voucher that has an e-invoice IRN from being converted into a Stock Journal or any other voucher type, except through a recorded and authorised exception |
| Version | 0.1, draft |

## 1. Status: read this first

This is a **draft for a Tally developer to verify, compile and test**. It has
**not** been compiled, loaded or run, because there is no TallyPrime or
TallyPrime Developer installation here. Specifically:

| Spec F deliverable | Status |
|---|---|
| TDL source | **Delivered:** [`TDL-INV-001.txt`](TDL-INV-001.txt) |
| Compiled deployment file (.tcp) | **Not delivered.** Compile it in TallyPrime Developer (section 5) |
| Field and event references verified against 7.1 | **Not done.** Section 6 lists every reference, what is known about it and how to verify it |
| Test results for every acceptance criterion | **Not done.** [`TEST-PROTOCOL.md`](TEST-PROTOCOL.md) has the test cases and expected results. The *Actual* column is blank and must be filled in from a real 7.1 run |
| Exclusions and known limitations | **Delivered:** section 7 |
| Written confirmation of 7.1 compatibility | **Not given.** It can only be signed after the test protocol passes (section 9) |
| Deployment and rollback instructions | **Delivered:** sections 5 and 8 |

Do not load this file in a live company until all section 6 references are
verified and the protocol has passed in a test company.

## 2. Files

| File | Purpose |
|---|---|
| `TDL-INV-001.txt` | TDL source. TallyPrime can load the `.txt` directly for testing. Production should use the compiled `.tcp` |
| `TEST-PROTOCOL.md` | Test cases, evidence standard, results sheet, sign-off |
| `README.md` | This file: design, traceability, deployment, references, limitations, rollback |

## 3. How the control works

**Trigger (spec A).** On every save (*Form Accept*) of the voucher form, the
TDL works out an outcome in `TDLInv001State`:

1. Not an alteration (a new voucher, or display mode)? **PASS.** Company data
   is not read at all, so voucher entry speed is unaffected.
2. It reads the **stored** copy of the voucher being altered, matched on
   `MasterID` from the company data, not from the voucher on screen. That copy
   counts only if its voucher type *belongs to* Sales (the predefined Sales
   type and every custom type under it) **and** it has an `IRN` or an
   `IRNAckNo`. "Either field" covers IRN details entered by hand through
   *Update e-Invoice details* as well as IRNs generated online. No such
   stored copy? **PASS.**
3. Is the voucher type at save time different from the stored type?
   That is a **CONVERSION**.
4. Type unchanged, but IRN and Ack No both blank on screen? That is an
   **IRNREMOVAL**. It closes the two-save bypass: clear the IRN and save, then
   convert a voucher the rule no longer recognises.
5. A CONVERSION or IRNREMOVAL becomes an **EXCEPTION** only when the user is on
   the authorised list **and** has filled in the exception panel.

**Blocking (spec B).** CONVERSION or IRNREMOVAL rejects the save. No save
handler runs, so the stored voucher stays unchanged and Edit Log records
nothing. An unauthorised user attempting a conversion sees exactly:

> This Sales voucher has an e-invoice IRN and is protected from voucher-type
> conversion. Contact the authorised finance controller.

**Authorised exceptions (spec D).**

- The list is the `TDLInv001IsAuthorised` formula at the top of the source.
  It ships as `No`, which means **nobody** is authorised. It names users
  explicitly, and Owner and Administrator users get no exemption. Changing it
  means changing the TDL, so it goes through the same approval and deployment
  as the code.
- For an authorised user in alteration mode, the voucher screen shows a
  panel at the bottom: **Reason**, **Approval reference** (approval memo,
  email or ticket number) and **Approved by**. All three are required. They
  are held for that one alteration only and start blank every time.
- On a permitted save, `TDLInv001Stamp` writes these UDFs to the voucher:
  action, username, date and time, original type, new type, original voucher
  number, original IRN, reason, approval reference, approver. The voucher
  keeps its MasterID through the conversion, so Edit Log holds the
  pre-conversion version (Sales, with IRN) and the stamped version together
  under the authorised user's name.

**Diagnostics.** **Ctrl+Alt+G** (*IRN Guard Check*) on any voucher shows what
the control sees: mode, MasterID, user, whether the user is authorised, the
current type, IRN and Ack No, the stored type, the outcome if the voucher were
saved now, and the last exception stamp. It changes nothing. It provides the
evidence for criteria E.1 and E.2.

## 4. Traceability to the specification

| Spec | Requirement | Where | Test |
|---|---|---|---|
| A.1 | Alteration of an existing voucher | `TDLInv001IsAlter` | T14 |
| A.2 | Original type before alteration | `TDLInv001OrigVch` (stored copy) | T01, T02 |
| A.3 | Proposed type at save | `$VoucherTypeName` in `TDLInv001State` | T02, T05 |
| A.4 | IRN on original, including manual update | `TDLInv001HasIRN` on the stored copy | T01, T06 |
| A.5 | User specifically authorised | `TDLInv001IsAuthorised` | T11, T15, T16 |
| B | Reject save with fixed message; original unchanged | `TDLInv001Reject`, save handler gated | T02 |
| C | Sales → Stock Journal | as B | T02 |
| C | Sales → any other type | any type difference blocks | T05, T07 |
| C | Repeated attempts | stateless check on every save | T08, T09 |
| C | Keyboard and UI paths | all end in Form Accept | T02–T04 |
| C | Import and other routes | **not covered by TDL**: compensating controls | T19, section 7 |
| D | Explicit list; no automatic admin exemption | `TDLInv001IsAuthorised` (fail-closed) | T11 |
| D | Record user, reference, reason, approval evidence | UDFs 7101–7110 + Edit Log | T16, T21 |
| E.1 | Inspect original state | stored copy by MasterID | T01, T09 |
| E.2 | Reliable IRN status | `IRN` / `IRNAckNo`, diagnostics | T01, T06 |
| E.3 | Reject, not warn | no save handler runs when blocked | T02 |
| E.4 | No bypass by changing the type first | original read from the company, plus the IRN-removal rule | T09, T10 |
| E.5 | Legitimate corrections still possible | exception panel | T15–T17 |
| E.6 | Works with existing TDLs and add-ons | **must be tested**: section 7, item 1 | T20 |
| E.7 | Source, deployment, tests, rollback | this folder | n/a |

## 5. Deployment

**Prerequisites**

1. TallyPrime Edit Log 7.1 on every machine (server, clients and remote
   users) that opens the company.
2. Company security on: *Alter Company → Control User Access to Company Data =
   Yes*, with a named login for every person. Without security every user
   name is blank, so nobody can use the exception path. That is intended.
3. A verified backup of each company.

**Steps**

1. **Approve the authorised list.** Edit `TDLInv001IsAuthorised` to name the
   approved usernames (see the example in the source) and file the approval.
2. **Verify the references** in section 6 using TallyPrime Developer 7.1 and a
   test company. Correct the source wherever 7.1 differs.
3. **Check UDF indices 7101–7110 and the Ctrl+Alt+G key** against every
   other TDL and add-on the company loads.
4. **Run [`TEST-PROTOCOL.md`](TEST-PROTOCOL.md)** in a test company, loading
   the `.txt` file: *F1 (Help) → TDLs & Add-ons → F4 Manage Local TDLs →
   Load selected TDL files on startup = Yes*, then add the full path.
5. **Compile** in TallyPrime Developer 7.1. The result must have zero errors
   and zero warnings. Keep the compiler output and the SHA-256 of both the
   `.txt` and the `.tcp` as evidence.
6. **Deploy the `.tcp`.** The preferred route is an **account-level TDL**
   through Tally's control centre, so that local users cannot unload it.
   Otherwise, load it on each machine as in step 4.
7. **Restart TallyPrime** on every machine. On each one, confirm under *F1 →
   TDLs & Add-ons* that TDL-INV-001 shows as loaded, then repeat T02 there.
8. **Put the compensating controls from section 7 in place** (import rights,
   HTTP/ODBC server) before calling the control live.

## 6. Platform reference register

Status key: **Doc** means confirmed in Tally's published documentation but not
yet on 7.1; **Unverified** means written from TDL convention and still to be
checked. Nothing here is verified on 7.1 yet.

| Ref | Reference used | Status | How to verify on 7.1 |
|---|---|---|---|
| R-01 | `[#Form: Voucher]` is the form used both to alter a Sales voucher and to save it after switching to Stock Journal or another type | Unverified | Find in the default TDL (TallyPrime Developer). If Stock Journal or any other target type saves through a different form, repeat the four `On : Form Accept` lines on that form |
| R-02 | `[#Report: Voucher]` holds report-scope variables for each alteration | Unverified | T15/T16: the panel starts blank on every alteration |
| R-03 | Once `On : Form Accept` is defined, the default save is suppressed. The 7.1 default `Form: Voucher` has no unconditional save handler of its own | Unverified, **critical** | Read the default TDL for `On : Form Accept` on `Form: Voucher` and its option forms. T02 must block |
| R-04 | Multiple `On : Form Accept` handlers run in the order written | Unverified | T16: the stamp is present after the save |
| R-05 | `$$InAlterMode` is true when altering a voucher, false when creating or displaying | Unverified | Diagnostics in create and alter mode (T01, T14) |
| R-06 | `MasterID` stays the same when the type is changed during alteration | Unverified | Diagnostics before and after switching type (T01) |
| R-07 | A `Vouchers : VoucherType` collection with `Child Of : $$VchTypeSales` and `Belongs To : Yes` returns the **stored** voucher (not the one on screen), and the period in context always covers its stored date | Unverified, **critical** | T01 (stored type still shows Sales after switching), T18 (date changed outside the period) |
| R-08 | `Parm Var` is evaluated once, on the requesting voucher | Unverified | T01: the stored copy is found |
| R-09 | Voucher methods `IRN` and `IRNAckNo` hold the IRN and Ack No, for both online and manually updated IRNs | **Doc** ([Tally e-invoice schema](https://help.tallysolutions.com/schema-changes-e-invoice/) lists `IRN`, `IRNAckNo`, `IRNAckDate`) | Export an e-invoiced voucher to XML and confirm the `<IRN>` and `<IRNACKNO>` tags. Compare with diagnostics (T01, T06) |
| R-10 | `$VoucherTypeName`, `$VoucherNumber` | Unverified (standard) | Diagnostics |
| R-11 | `$$CmpUserName` returns the logged-in company user | Unverified | Diagnostics as each test user |
| R-12 | `$$IsEmpty`, `$$CollectionField`, `$$VchTypeSales`, `$$String`, `$$MachineDate`, `$$MachineTime`, `$$NewLine` | Unverified (standard) | Compiles clean; diagnostics shows the expected values |
| R-13 | `SET VALUE` in a function called from Form Accept writes to the voucher being saved; `WALK COLLECTION`, `MSG BOX`, `Call` with a parameter | Unverified | T16: UDFs present after the save |
| R-14 | UDF indices 7101–7110 are free | Unverified | Check against all loaded TDLs and add-ons (ask vendors of compiled add-ons) |
| R-15 | Ctrl+Alt+G is free on the voucher screen | Unverified | Press it with all add-ons loaded |
| R-16 | `Add : Bottom Part`, `Invisible`, `Modifies` behave as written | Unverified | T15: panel visible only to authorised users in alteration |

## 7. Exclusions and known limitations

**Risks to clear before go-live**

1. **Other add-ons can defeat the block (E.6).** If any other loaded TDL
   gives `Form: Voucher` an unconditional `On : Form Accept : Yes : Form
   Accept`, that handler saves even when this TDL has rejected. Review every
   loaded TDL. For compiled add-ons, get the vendor's written answer. Any such
   handler must also be gated on `$$TDLInv001AllowSave`. T20 tests this.
2. **Stored-copy lookup (R-07).** If 7.1 returns the on-screen voucher, or
   limits the lookup to a period that misses the stored date, the control
   **fails open** (allows the save). T01 and T18 are designed to catch this.
   Do not go live without them passing.
3. **Field names (R-09).** If 7.1 stores the IRN under a different method,
   every voucher looks IRN-free and the control fails open. T01 catches this.

**Routes this TDL does not cover (compensating controls required)**

4. **Import and integrations.** XML/JSON/Excel import (*Alt+O*), the
   TallyPrime HTTP/XML server (port 9000), ODBC, and third-party
   connectors that post vouchers do not go through the voucher form. **The
   control does not fire on them.** To compensate: deny Import to every
   non-authorised security level; set *F1 → Settings → Connectivity →
   TallyPrime acts as* to *None* or *Client* unless an integration needs it,
   and list any integration that does. T19 records the result.
5. **Machines without the TDL.** A client or remote user that has not loaded
   it is not protected. Deploying it as an account-level TDL addresses this.
6. **Unloading the TDL.** A user who can manage local TDLs can remove it.
   Again, use an account-level TDL and restrict who can manage TDLs.
7. **Other forms that edit e-invoice details.** The IRN-removal rule covers
   the voucher form only. If 7.1 lets IRN details be cleared from another
   screen (for example the e-Invoice report's update screen), the two-save
   bypass is open through that screen. Identify those screens in testing
   (T10) and restrict them.
8. **Voucher type master alteration.** Changing a custom Sales voucher
   type's parent type changes every voucher under it. Restrict alteration of
   Voucher Type masters through security levels.

**Out of scope by specification (separate controls needed)**

9. Deletion, cancellation (voucher cancellation and IRN cancellation),
   duplication, and creating a replacement voucher. Note that *delete the
   Sales voucher, then enter a Stock Journal* achieves the same result as a
   conversion and is not blocked here.

**Design choices to confirm with the client**

10. **IRN cancellation.** Protection follows the stored IRN and Ack No. If
    7.1 keeps them after an IRN is cancelled, the voucher stays protected. If
    it blanks them, the voucher stops being protected. T22 records which
    applies, and whether the IRN-removal rule gets in the way of Tally's
    standard cancellation flow.
11. **All type changes are blocked**, including a change to another Sales
    type. Any change the policy allows goes through the exception panel.
12. **Blocked attempts are not logged.** They are never saved, so Edit Log
    has no record of them. Logging attempts would be a separate change.
13. **Administrator impersonation.** A TallyPrime administrator can reset an
    authorised user's password and log in as that user. TDL cannot prevent
    this. Keep the Tally administrator role separate from the authorised
    finance controllers and review Edit Log for exceptions.
14. **Performance.** Each alteration save reads the company's Sales vouchers
    in the current period: four times, or five on an authorised exception.
    Voucher creation does not read them at all. T24 measures the cost on the
    largest company.

## 8. Rollback

1. Remove TDL-INV-001: either from the account-level TDL configuration, or
   from *F1 → TDLs & Add-ons → F4* on each machine. Restart TallyPrime
   everywhere.
2. Confirm *F1 → TDLs & Add-ons* no longer lists it, and that the
   Ctrl+Alt+G button has gone from the voucher screen.
3. **Data.** The TDL writes nothing except the exception UDFs on authorised
   saves. Those values stay in the vouchers under indices 7101–7110, hidden
   while the TDL is unloaded and visible again if it is reloaded. They have
   no effect on accounts or statutory reports. **Never reuse those indices in
   another TDL.**
4. Edit Log history is not affected.
5. Restoring the pre-deployment backup is needed only if data corruption is
   found. None is expected from this TDL.
6. Record the date of the rollback, who did it, why, and the result of a
   repeat of T25.

## 9. Compatibility confirmation

No confirmation of compatibility with TallyPrime Edit Log 7.1 is given in
this document. The developer completes the sign-off at the end of
`TEST-PROTOCOL.md` only after every test there has passed on 7.1 with the
production set of TDLs and add-ons loaded.
