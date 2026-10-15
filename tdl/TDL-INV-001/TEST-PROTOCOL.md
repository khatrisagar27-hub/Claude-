# TDL-INV-001: test protocol

Run on **TallyPrime Edit Log 7.1** in an **isolated test company**. Load the
`.txt` file for T01–T19, T21, T22, T24 and T25. Load the compiled `.tcp`,
together with the production set of TDLs and add-ons, for T20 and T23. Fill
in the results sheet (section 4) from the actual run. Nothing in this file is
a result until that is done.

## 1. Test setup

**Company.** Restore a backup of a live company under a separate data path,
and never sync it back. This gives real online-generated IRNs, which a fresh
test company cannot produce. Turn on *Control User Access to Company Data*.

**Users**

| ID | Security level | On authorised list? |
|---|---|---|
| U-DE | Data entry, with voucher alteration rights | No |
| U-ADMIN | Owner or Administrator | No |
| U-AUTH | Finance controller | Yes. Put this name in `TDLInv001IsAuthorised` for the test |

**Vouchers.** Note the number, date and MasterID of each, using
diagnostics (Ctrl+Alt+G).

| ID | Description |
|---|---|
| V1 | Predefined *Sales* type, IRN generated online |
| V2 | Sales, IRN entered manually via *Update e-Invoice details* |
| V3 | Custom voucher type under Sales (e.g. "Sales B2B"), with IRN |
| V4 | Sales, no IRN |
| V5 | Stock Journal (not Sales) |
| V6 | Sales with IRN, dated in a different month from V1 |

**Evidence standard.** Each test needs a screenshot showing the logged-in
user, the system date and time, and the message or result. Where noted, add
an XML export of the voucher (or an Edit Log screen). Name the files
`T<nn>-<step>.png` / `.xml`.

## 2. Baseline (before loading the TDL)

**T00.** As U-DE, convert a *copy* of an IRN Sales voucher to Stock Journal and
save. Record that it succeeds. This proves the risk exists on this
installation and that any later block comes from the TDL. Restore the test
company afterwards.

## 3. Test cases

| ID | Spec | User | Steps | Expected |
|---|---|---|---|---|
| T01 | A.2, A.4, E.1, E.2; R-05–R-09 | U-DE | Open V1, V2, V3, V4 in alteration and press Ctrl+Alt+G. On V1, switch the type to Stock Journal and press Ctrl+Alt+G again. Export V1–V4 to XML | IRN and Ack No in diagnostics match the `<IRN>` / `<IRNACKNO>` XML tags. The stored type shows for V1–V3 and is blank for V4. After the switch, MasterID is unchanged, the stored type still reads Sales, and the outcome is CONVERSION |
| T02 | B, C, E.3 | U-DE | V1: switch to Stock Journal, then Ctrl+A. Esc, discard. Reopen V1 | The exact spec B message appears and no save happens. On reopening, V1 is still Sales with its IRN, and Edit Log shows no new version |
| T03 | C (keyboard) | U-DE | As T02, but Enter through every field to *Accept? Yes* | Blocked, same message |
| T04 | C (UI) | U-DE | As T02, but accept with the mouse | Blocked, same message |
| T05 | C | U-DE | V1 → Journal, Receipt, Credit Note, Delivery Note, and another Sales type, each saved separately | Each one blocked |
| T06 | A.4 | U-DE | V2 → Stock Journal | Blocked |
| T07 | C | U-DE | V3 → Stock Journal | Blocked |
| T08 | C | U-DE | In one alteration session on V1, try five saves after switching to Stock Journal, each time also changing something else (date, narration, an amount) | All five blocked. The stored V1 is unchanged |
| T09 | E.4 | U-DE | V1: Sales → Stock Journal → Sales → Journal, then save. Then Sales → Stock Journal → back to Sales, and save | First save blocked (final type differs). Second save succeeds (no conversion) |
| T10 | E.4 | U-DE | V1: blank IRN and Ack No, save. Then switch to Stock Journal and save. Repeat the blanking from any other screen that can edit e-invoice details | Both saves are blocked: the first with the IRN-removal message, the second with the spec B message. List every other screen found, with its result |
| T11 | D | U-ADMIN | V1 → Stock Journal | Blocked with the spec B message, and no exception panel is shown |
| T12 | Scope | U-DE | V1: change only the narration and save | Saves normally |
| T13 | Scope | U-DE | V4 (no IRN) → Stock Journal | Saves. The voucher is outside this control's scope |
| T14 | A.1 | U-DE, U-AUTH | Create a new Sales voucher and a new Stock Journal | Both save normally. No panel appears. Diagnostics show *Alteration mode = No* |
| T15 | E.5 | U-AUTH | V1 → Stock Journal with the panel left blank. Then fill in only the Reason | Blocked with the approval-required message both times. The panel is visible |
| T16 | D, E.5; R-04, R-13 | U-AUTH | V1 → Stock Journal with Reason, Approval reference and Approved by filled in, then save. Reopen and press Ctrl+Alt+G. Export to XML | Saves. Diagnostics and XML show all 10 UDFs with the right values (user U-AUTH, original type Sales, original number, original IRN) |
| T17 | D | U-AUTH | V6: change the narration only, panel blank | Saves. No UDFs written |
| T18 | R-07 | U-DE | Set Day Book to V6's date only. Alter V6: change the date to another month and switch to Stock Journal. Repeat after opening V6 from a ledger report set to a different period | Blocked both times |
| T19 | C (import) | U-DE | Export V1 to XML, change the voucher type to Stock Journal, and import it with alter/replace into the test company. Repeat over the HTTP port if the server is enabled | **Expected limitation:** the TDL does not block this. Record the outcome. Then confirm the compensating controls: U-DE cannot reach Import, and HTTP posts are refused when the server is off |
| T20 | E.6 | U-DE, U-AUTH | Load the `.tcp` with every production TDL and add-on, in production order. Check *F1 → TDLs & Add-ons*. Repeat T02, T12 and T16. Exercise each add-on's own voucher-save features | Everything loads with no errors. T02 still blocks. T12 and T16 still pass. The add-ons work as before |
| T21 | D | Reviewer | After T16, open Edit Log for V1 | The Sales version with IRN and the Stock Journal version with the UDFs are both present, the alteration is attributed to U-AUTH, and it carries a timestamp |
| T22 | Limitation 10 | U-DE | Cancel the IRN of a test voucher using Tally's standard flow (online or offline cancellation) | Record whether IRN and Ack No are retained, and whether the IRN-removal rule interfered. Decide the policy |
| T23 | Limitation 5 | each | On every client machine and remote user, repeat T02 | Blocked everywhere |
| T24 | Limitation 14 | U-DE | On the largest company, with the Day Book set to the full year, time an alteration save of a Sales voucher before and after loading the TDL | Record both times. The client sets the acceptance threshold |
| T25 | Rollback | U-DE | Unload the TDL and repeat T02 on a copy. Reload it and repeat T02 | Not blocked while unloaded; blocked again once reloaded |

## 4. Results sheet

| ID | Actual result | Pass / Fail | Evidence files | Tester | Date |
|---|---|---|---|---|---|
| T00 | | | | | |
| T01 | | | | | |
| T02 | | | | | |
| T03 | | | | | |
| T04 | | | | | |
| T05 | | | | | |
| T06 | | | | | |
| T07 | | | | | |
| T08 | | | | | |
| T09 | | | | | |
| T10 | | | | | |
| T11 | | | | | |
| T12 | | | | | |
| T13 | | | | | |
| T14 | | | | | |
| T15 | | | | | |
| T16 | | | | | |
| T17 | | | | | |
| T18 | | | | | |
| T19 | | | | | |
| T20 | | | | | |
| T21 | | | | | |
| T22 | | | | | |
| T23 | | | | | |
| T24 | | | | | |
| T25 | | | | | |

Any failure: fix the source, recompile, and rerun the **whole** protocol.
Rerunning only the failed test is not enough.

## 5. Sign-off and compatibility confirmation

> I confirm that TDL-INV-001 version ____, source SHA-256 ____________,
> compiled file SHA-256 ____________, was tested on TallyPrime Edit Log
> Release 7.1 (build ______), with the following TDLs and add-ons loaded:
> ______________________. All references in README section 6 were verified,
> with these corrections: ______________. All tests in section 3 passed
> except: ______________ (with the disposition of each).

| Role | Name | Signature | Date |
|---|---|---|---|
| TDL developer | | | |
| Tester (independent of developer) | | | |
| Finance controller (control owner) | | | |
| Internal audit (reviewed) | | | |
