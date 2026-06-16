Attribute VB_Name = "LexComply"
Option Explicit

' ================================================================
'  LexComply India — Indian Law Compliance Analyzer
'  VBA Module  |  52+ Indian Laws  |  All 10 Categories
'  Usage: Alt+F11 → Import this .bas → Click "Analyze" button
' ================================================================

' ── Colours ──
Private Const C_CRIT_FG  As Long = 12910848  ' RGB(220,38,38)
Private Const C_CRIT_BG  As Long = 14483711  ' RGB(254,226,226) - light red tint; use ~FEE2E2
Private Const C_HIGH_FG  As Long = 431470    ' RGB(217,119,6)
Private Const C_HIGH_BG  As Long = 13697535  ' ~FEF3C7
Private Const C_MED_FG   As Long = 8404994   ' RGB(2,132,199)
Private Const C_MED_BG   As Long = 16117472  ' ~E0F2FE
Private Const C_LOW_FG   As Long = 6942311   ' RGB(5,150,105)
Private Const C_LOW_BG   As Long = 14811617  ' ~D1FAE5
Private Const C_NAVY     As Long = 2957832   ' RGB(13,27,46)
Private Const C_BLUE     As Long = 14287645  ' RGB(29,78,216)
Private Const C_GOLD     As Long = 5348552   ' RGB(200,169,81)
Private Const C_WHITE    As Long = 16777215
Private Const C_LTGRAY   As Long = 15921906  ' RGB(242,242,242)
Private Const C_DGRAY    As Long = 8026754   ' RGB(130,130,130)

' ── Profile Variables (populated by ReadInputs) ──
Private mCompanyName As String
Private mEntityType  As String
Private mStateOfReg  As String
Private mStatesOp    As String
Private mSector      As String
Private mTurnover    As Long     ' lakhs
Private mNetWorth    As Long     ' crores
Private mNetProfit   As Long     ' crores
Private mPaidUpCap   As Long     ' crores
Private mTotalEmp    As Long
Private mContractW   As Long
Private mWomenEmp    As Long
Private mMigrantW    As Long
Private mFactoryW    As Long
Private mPWDEmp      As Long
Private mIsListed    As Boolean
Private mHasFDI      As Boolean
Private mImportExp   As Boolean
Private mIsMSME      As Boolean
Private mHasForex    As Boolean
Private mHasFactory  As Boolean
Private mFactPower   As Boolean
Private mHasShop     As Boolean
Private mIsManuf     As Boolean
Private mIsTrading   As Boolean
Private mIsEComm     As Boolean
Private mFoodBev     As Boolean
Private mPharma      As Boolean
Private mPetroleum   As Boolean
Private mExplosives  As Boolean
Private mChemicals   As Boolean
Private mBoilers     As Boolean
Private mMines       As Boolean
Private mConstruct   As Boolean
Private mRealEstate  As Boolean
Private mNBFC        As Boolean
Private mInsurance   As Boolean
Private mBanking     As Boolean
Private mHazWaste    As Boolean
Private mEWaste      As Boolean
Private mPlastic     As Boolean
Private mWaterDisc   As Boolean
Private mAirEmit     As Boolean
Private mLargeElec   As Boolean
Private mHasWeb      As Boolean
Private mCollData    As Boolean
Private mHasPayment  As Boolean
Private mIsIT        As Boolean
Private mIsPMLA      As Boolean
Private mHasIP       As Boolean
Private mApprentices As Boolean

' ── Sheet Row Counters ──
Private rLaws    As Long   ' Laws Overview sheet
Private rCheck   As Long   ' Checklist sheet
Private rCal     As Long   ' Calendar sheet
Private rUrgent  As Long   ' Urgent sheet
Private rSr      As Long   ' Serial number counter

' ── Sheet references ──
Private wsProfile As Worksheet
Private wsLaws    As Worksheet
Private wsCheck   As Worksheet
Private wsCal     As Worksheet
Private wsUrgent  As Worksheet
Private wsDash    As Worksheet

' ================================================================
'  MAIN ENTRY POINT — wire this to the "Analyze Compliance" button
' ================================================================
Public Sub AnalyzeCompliance()
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual

    On Error GoTo ErrHandler

    Set wsProfile = ThisWorkbook.Worksheets("Company Profile")
    Set wsLaws    = ThisWorkbook.Worksheets("Laws Overview")
    Set wsCheck   = ThisWorkbook.Worksheets("Compliance Checklist")
    Set wsCal     = ThisWorkbook.Worksheets("Compliance Calendar")
    Set wsUrgent  = ThisWorkbook.Worksheets("Urgent Actions")
    Set wsDash    = ThisWorkbook.Worksheets("Dashboard")

    Call ReadInputs
    Call ClearOutputSheets
    Call WriteSheetHeaders
    Call RunAllLaws

    ' Finalise
    wsLaws.Columns.AutoFit
    wsCheck.Columns.AutoFit
    wsCal.Columns.AutoFit
    wsUrgent.Columns.AutoFit
    wsLaws.Range("A1").Select

    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True

    Dim lawCount As Long
    lawCount = rLaws - 3
    MsgBox "Analysis complete!" & vbCrLf & vbCrLf & _
           mCompanyName & " has " & lawCount & " applicable Indian laws." & vbCrLf & _
           "See each sheet tab for details." & vbCrLf & vbCrLf & _
           "TIP: Review the 'Urgent Actions' tab first.", _
           vbInformation, "LexComply India"

    wsLaws.Activate
    Exit Sub

ErrHandler:
    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True
    MsgBox "Error: " & Err.Description & vbCrLf & "Line: " & Erl, vbCritical, "LexComply"
End Sub

' ================================================================
'  READ INPUTS from Company Profile sheet named ranges
' ================================================================
Private Sub ReadInputs()
    Dim ws As Worksheet
    Set ws = wsProfile

    mCompanyName = Trim(ws.Range("inp_CompanyName").Value)
    mEntityType  = Trim(ws.Range("inp_EntityType").Value)
    mStateOfReg  = Trim(ws.Range("inp_StateOfReg").Value)
    mStatesOp    = LCase(Trim(ws.Range("inp_StatesOp").Value))
    mSector      = LCase(Trim(ws.Range("inp_Sector").Value))
    mTurnover    = CLngSafe(ws.Range("inp_Turnover").Value)
    mNetWorth    = CLngSafe(ws.Range("inp_NetWorth").Value)
    mNetProfit   = CLngSafe(ws.Range("inp_NetProfit").Value)
    mPaidUpCap   = CLngSafe(ws.Range("inp_PaidUpCap").Value)
    mTotalEmp    = CLngSafe(ws.Range("inp_TotalEmp").Value)
    mContractW   = CLngSafe(ws.Range("inp_ContractW").Value)
    mWomenEmp    = CLngSafe(ws.Range("inp_WomenEmp").Value)
    mMigrantW    = CLngSafe(ws.Range("inp_MigrantW").Value)
    mFactoryW    = CLngSafe(ws.Range("inp_FactoryW").Value)
    mPWDEmp      = CLngSafe(ws.Range("inp_PWDEmp").Value)

    mIsListed    = IsYes(ws.Range("inp_IsListed").Value)
    mHasFDI      = IsYes(ws.Range("inp_HasFDI").Value)
    mImportExp   = IsYes(ws.Range("inp_ImportExp").Value)
    mIsMSME      = IsYes(ws.Range("inp_IsMSME").Value)
    mHasForex    = IsYes(ws.Range("inp_HasForex").Value)
    mHasFactory  = IsYes(ws.Range("inp_HasFactory").Value)
    mFactPower   = IsYes(ws.Range("inp_FactPower").Value)
    mHasShop     = IsYes(ws.Range("inp_HasShop").Value)
    mIsManuf     = IsYes(ws.Range("inp_IsManuf").Value)
    mIsTrading   = IsYes(ws.Range("inp_IsTrading").Value)
    mIsEComm     = IsYes(ws.Range("inp_IsEComm").Value)
    mFoodBev     = IsYes(ws.Range("inp_FoodBev").Value)
    mPharma      = IsYes(ws.Range("inp_Pharma").Value)
    mPetroleum   = IsYes(ws.Range("inp_Petroleum").Value)
    mExplosives  = IsYes(ws.Range("inp_Explosives").Value)
    mChemicals   = IsYes(ws.Range("inp_Chemicals").Value)
    mBoilers     = IsYes(ws.Range("inp_Boilers").Value)
    mMines       = IsYes(ws.Range("inp_Mines").Value)
    mConstruct   = IsYes(ws.Range("inp_Construct").Value)
    mRealEstate  = IsYes(ws.Range("inp_RealEstate").Value)
    mNBFC        = IsYes(ws.Range("inp_NBFC").Value)
    mInsurance   = IsYes(ws.Range("inp_Insurance").Value)
    mBanking     = IsYes(ws.Range("inp_Banking").Value)
    mHazWaste    = IsYes(ws.Range("inp_HazWaste").Value)
    mEWaste      = IsYes(ws.Range("inp_EWaste").Value)
    mPlastic     = IsYes(ws.Range("inp_Plastic").Value)
    mWaterDisc   = IsYes(ws.Range("inp_WaterDisc").Value)
    mAirEmit     = IsYes(ws.Range("inp_AirEmit").Value)
    mLargeElec   = IsYes(ws.Range("inp_LargeElec").Value)
    mHasWeb      = IsYes(ws.Range("inp_HasWeb").Value)
    mCollData    = IsYes(ws.Range("inp_CollData").Value)
    mHasPayment  = IsYes(ws.Range("inp_HasPayment").Value)
    mIsIT        = IsYes(ws.Range("inp_IsIT").Value)
    mIsPMLA      = IsYes(ws.Range("inp_IsPMLA").Value)
    mHasIP       = IsYes(ws.Range("inp_HasIP").Value)
    mApprentices = IsYes(ws.Range("inp_Apprentices").Value)

    ' Derive sector booleans
    If InStr(mSector, "manufacturing") > 0 Or InStr(mSector, "manufactur") > 0 Then mIsManuf = True
    If InStr(mSector, "ecommerce") > 0 Or InStr(mSector, "e-commerce") > 0 Then mIsEComm = True
    If InStr(mSector, "food") > 0 Then mFoodBev = True
    If InStr(mSector, "pharma") > 0 Then mPharma = True
    If InStr(mSector, "realestate") > 0 Or InStr(mSector, "real estate") > 0 Then mRealEstate = True
    If InStr(mSector, "mining") > 0 Then mMines = True
    If InStr(mSector, "nbfc") > 0 Then mNBFC = True
    If InStr(mSector, "insurance") > 0 Then mInsurance = True
    If InStr(mSector, "banking") > 0 Then mBanking = True
    If InStr(mSector, "it") > 0 Or InStr(mSector, "software") > 0 Then mIsIT = True
End Sub

Private Function CLngSafe(v As Variant) As Long
    On Error Resume Next
    If IsNumeric(v) Then CLngSafe = CLng(v) Else CLngSafe = 0
    On Error GoTo 0
End Function

Private Function IsYes(v As Variant) As Boolean
    IsYes = (LCase(Trim(CStr(v))) = "yes")
End Function

Private Function HasState(stateName As String) As Boolean
    HasState = (InStr(mStatesOp, LCase(stateName)) > 0)
End Function

' ================================================================
'  CLEAR OUTPUT SHEETS
' ================================================================
Private Sub ClearOutputSheets()
    Dim ws As Worksheet
    For Each ws In Array(wsLaws, wsCheck, wsCal, wsUrgent, wsDash)
        ws.Cells.Clear
        ws.Cells.Interior.ColorIndex = xlNone
        ws.Cells.Font.Color = C_NAVY
    Next ws
    rLaws = 3 : rCheck = 3 : rCal = 3 : rUrgent = 3 : rSr = 1
End Sub

' ================================================================
'  WRITE SHEET HEADERS
' ================================================================
Private Sub WriteSheetHeaders()
    Dim today As String
    today = Format(Now(), "DD-MMM-YYYY")

    ' ── Laws Overview ──
    With wsLaws
        .Name = "Laws Overview"
        MergeHdr .Range("A1:G1"), "LexComply India — Laws Overview  |  " & mCompanyName & "  |  " & today
        MergeHdr .Range("A2:G2"), "All laws applicable to the company based on the profile provided"
        Call ColHdr(wsLaws, 3, Array("#", "Priority", "Law / Act", "Category", "Why Applicable", "Actions", "Key Authority"))
        .Columns("A").ColumnWidth = 5
        .Columns("B").ColumnWidth = 12
        .Columns("C").ColumnWidth = 42
        .Columns("D").ColumnWidth = 18
        .Columns("E").ColumnWidth = 38
        .Columns("F").ColumnWidth = 8
        .Columns("G").ColumnWidth = 28
    End With

    ' ── Compliance Checklist ──
    With wsCheck
        .Name = "Compliance Checklist"
        MergeHdr .Range("A1:J1"), "LexComply India — Master Compliance Checklist  |  " & mCompanyName & "  |  " & today
        MergeHdr .Range("A2:J2"), "Every compliance action required — with deadline, authority, and penalty"
        Call ColHdr(wsCheck, 3, Array("Sr.", "Priority", "Law Name", "Category", "Action Required", "Frequency", "Deadline", "Authority", "Penalty", "Status"))
        .Columns("A").ColumnWidth = 5
        .Columns("B").ColumnWidth = 12
        .Columns("C").ColumnWidth = 32
        .Columns("D").ColumnWidth = 16
        .Columns("E").ColumnWidth = 44
        .Columns("F").ColumnWidth = 14
        .Columns("G").ColumnWidth = 26
        .Columns("H").ColumnWidth = 28
        .Columns("I").ColumnWidth = 32
        .Columns("J").ColumnWidth = 12
    End With

    ' ── Calendar ──
    With wsCal
        .Name = "Compliance Calendar"
        MergeHdr .Range("A1:F1"), "LexComply India — Compliance Calendar (by Frequency)  |  " & mCompanyName
        MergeHdr .Range("A2:F2"), "Actions grouped by how often they recur"
        .Columns("A").ColumnWidth = 12
        .Columns("B").ColumnWidth = 30
        .Columns("C").ColumnWidth = 44
        .Columns("D").ColumnWidth = 26
        .Columns("E").ColumnWidth = 26
        .Columns("F").ColumnWidth = 32
    End With

    ' ── Urgent ──
    With wsUrgent
        .Name = "Urgent Actions"
        MergeHdr .Range("A1:G1"), "LexComply India — URGENT: Critical & High Priority  |  " & mCompanyName
        MergeHdr .Range("A2:G2"), "Address these FIRST — highest penalty and legal risk"
        Call ColHdr(wsUrgent, 3, Array("Priority", "Law Name", "Action Required", "Deadline", "Penalty", "Authority", "Done?"))
        .Columns("A").ColumnWidth = 12
        .Columns("B").ColumnWidth = 30
        .Columns("C").ColumnWidth = 44
        .Columns("D").ColumnWidth = 26
        .Columns("E").ColumnWidth = 32
        .Columns("F").ColumnWidth = 26
        .Columns("G").ColumnWidth = 10
    End With

    ' ── Dashboard ──
    BuildDashboard
End Sub

Private Sub MergeHdr(rng As Range, txt As String)
    With rng
        .Merge
        .Value = txt
        .Font.Bold = True
        .Font.Color = C_WHITE
        .Font.Size = IIf(rng.Row = 1, 13, 10)
        .Interior.Color = C_NAVY
        .RowHeight = IIf(rng.Row = 1, 32, 18)
        .HorizontalAlignment = xlLeft
        .VerticalAlignment = xlCenter
        .IndentLevel = 1
    End With
End Sub

Private Sub ColHdr(ws As Worksheet, r As Long, hdrs As Variant)
    Dim i As Integer
    For i = 0 To UBound(hdrs)
        With ws.Cells(r, i + 1)
            .Value = hdrs(i)
            .Font.Bold = True
            .Font.Color = C_WHITE
            .Font.Size = 9
            .Interior.Color = C_BLUE
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
            .WrapText = True
            .RowHeight = 28
        End With
    Next i
End Sub

' ================================================================
'  DASHBOARD SHEET
' ================================================================
Private Sub BuildDashboard()
    With wsDash
        .Name = "Dashboard"
        MergeHdr .Range("A1:F1"), "  ⚖  LexComply India — Compliance Dashboard"
        .Range("A1").Font.Size = 16

        ' Company info block
        Dim r As Long
        r = 3
        DashLabel wsDash, r, "Company", mCompanyName
        DashLabel wsDash, r + 1, "Entity Type", mEntityType
        DashLabel wsDash, r + 2, "State of Registration", mStateOfReg
        DashLabel wsDash, r + 3, "Primary Sector", mSector
        DashLabel wsDash, r + 4, "Annual Turnover", TurnoverLabel(mTurnover)
        DashLabel wsDash, r + 5, "Total Employees", CStr(mTotalEmp)
        DashLabel wsDash, r + 6, "Report Date", Format(Now(), "DD-MMM-YYYY HH:MM")

        ' Stats will be filled after RunAllLaws
        .Range("A11").Value = "COMPLIANCE SUMMARY"
        .Range("A11").Font.Bold = True
        .Range("A11").Font.Color = C_GOLD
        .Columns("A").ColumnWidth = 22
        .Columns("B").ColumnWidth = 38
        .Columns("C").ColumnWidth = 16
        .Columns("D").ColumnWidth = 16
        .Columns("E").ColumnWidth = 16
        .Columns("F").ColumnWidth = 16
    End With
End Sub

Private Sub DashLabel(ws As Worksheet, r As Long, lbl As String, val As String)
    With ws.Cells(r, 1)
        .Value = lbl & ":"
        .Font.Bold = True
        .Font.Color = C_DGRAY
        .Font.Size = 9
    End With
    With ws.Cells(r, 2)
        .Value = val
        .Font.Color = C_NAVY
        .Font.Size = 10
    End With
End Sub

Private Function TurnoverLabel(t As Long) As String
    Select Case t
        Case 0:       TurnoverLabel = "Below ₹20 Lakhs"
        Case 20:      TurnoverLabel = "₹20 – ₹40 Lakhs"
        Case 40:      TurnoverLabel = "₹40 Lakhs – ₹1 Crore"
        Case 100:     TurnoverLabel = "₹1 – ₹10 Crore"
        Case 1000:    TurnoverLabel = "₹10 – ₹100 Crore"
        Case 10000:   TurnoverLabel = "₹100 – ₹500 Crore"
        Case 50000:   TurnoverLabel = "₹500 – ₹1000 Crore"
        Case 100000:  TurnoverLabel = "Above ₹1000 Crore"
        Case Else:    TurnoverLabel = CStr(t) & " Lakhs"
    End Select
End Function

' ================================================================
'  CORE: RUN ALL LAWS
' ================================================================
Private Sub RunAllLaws()
    rLaws = 4 : rCheck = 4 : rCal = 4 : rUrgent = 4 : rSr = 1

    ' ── A. SOCIAL SECURITY ──────────────────────────────────────
    If mTotalEmp >= 20 Then
        Dim r1 As String: r1 = "Total employees " & mTotalEmp & " ≥ 20 (mandatory threshold)"
        L wsLaws, "critical", "Employees' Provident Fund & Miscellaneous Provisions Act, 1952", "Social Security", r1, 5, "EPFO"
        A "EPF Act", "critical", "Register establishment with EPFO (get PF Code)", "One-time", "Within 30 days of reaching 20 employees", "EPFO Regional Office / Shram Suvidha Portal", "Damages @ 5–25% of arrears + imprisonment up to 3 years"
        A "EPF Act", "critical", "Deduct 12% of Basic+DA from employee wages (EPF contribution)", "Monthly", "15th of following month", "EPFO", "Interest @ 12% p.a. + damages"
        A "EPF Act", "critical", "Employer contributes 12% (EPS 8.33% + EPF 3.67%)", "Monthly", "15th of following month", "EPFO", "Damages + interest on arrears"
        A "EPF Act", "critical", "File Electronic Challan cum Return (ECR) online", "Monthly", "15th of following month", "EPFO Unified Portal", "₹5,000 per day of delay"
        A "EPF Act", "critical", "Issue UAN (Universal Account Number) to every employee; seed Aadhaar + PAN + bank", "One-time per employee", "At time of joining", "EPFO", "Compliance issue"
    End If

    If (mHasFactory And mFactoryW >= 10) Or (Not mHasFactory And mTotalEmp >= 20) Then
        Dim r2 As String
        If mHasFactory Then r2 = "Factory with " & mFactoryW & " workers (threshold: 10)"
        Else r2 = "Establishment with " & mTotalEmp & " employees (threshold: 20)"
        L wsLaws, "critical", "Employees' State Insurance Act, 1948", "Social Security", r2, 5, "ESIC"
        A "ESI Act", "critical", "Register establishment with ESIC; obtain Employer Code", "One-time", "Within 15 days of applicability", "ESIC Regional Office", "Imprisonment up to 2 years + fine up to ₹5,000"
        A "ESI Act", "critical", "Deduct employee's ESI contribution @ 0.75% of gross wages", "Monthly", "15th of following month", "ESIC", "Damages + 12% p.a. interest"
        A "ESI Act", "critical", "Pay employer's ESI contribution @ 3.25% of gross wages", "Monthly", "15th of following month", "ESIC", "Damages + interest"
        A "ESI Act", "critical", "File half-yearly returns (Form 5)", "Half-yearly", "11 November and 11 May", "ESIC", "Fine"
        A "ESI Act", "critical", "Report workplace accidents within 24 hours", "As required", "Within 24 hours of accident", "ESIC Local Office", "Fine"
    End If

    If mTotalEmp >= 10 Then
        L wsLaws, "critical", "Payment of Gratuity Act, 1972", "Social Security", "Employees = " & mTotalEmp & " (threshold: 10; once applicable, always applicable)", 4, "Labour Commissioner"
        A "Gratuity Act", "critical", "Pay gratuity on resignation/retirement/death (5+ years service)", "As applicable", "Within 30 days of becoming due", "Labour Commissioner", "10% p.a. interest + fine up to ₹1 lakh; imprisonment up to 2 years"
        A "Gratuity Act", "critical", "Obtain gratuity insurance (LIC Group Gratuity) or create approved trust", "Annual renewal", "Within 1 year of applicability", "Labour Commissioner / LIC", "Fine"
        A "Gratuity Act", "critical", "Collect nomination form (Form F) from every employee", "One-time per employee", "Within 30 days of joining", "Employer records", "Fine"
        A "Gratuity Act", "critical", "Notify Controlling Authority (Form A or B)", "One-time", "On applicability", "Labour Department", "Fine"
    End If

    If mTotalEmp >= 20 Then
        L wsLaws, "high", "Payment of Bonus Act, 1965", "Labour", "Employees = " & mTotalEmp & " (threshold: 20)", 3, "Labour Department"
        A "Bonus Act", "high", "Pay minimum bonus 8.33% of annual wages (or ₹100, whichever higher) — eligible employees earning ≤ ₹21,000/month", "Annual", "Within 8 months of close of accounting year", "Labour Department", "Imprisonment up to 6 months + fine up to ₹1,000"
        A "Bonus Act", "high", "Maintain bonus registers Form A (computation), Form B (set-on/off), Form C (paid)", "Annual", "On computation / payment", "Labour Department", "Fine"
        A "Bonus Act", "high", "File annual bonus return (Form D)", "Annual", "Within 30 days of bonus payment", "Labour Commissioner", "Fine"
    End If

    If mWomenEmp > 0 Then
        L wsLaws, "high", "Maternity Benefit Act, 1961", "Labour", "Company employs " & mWomenEmp & " women employees", 4, "Labour Department"
        A "Maternity Act", "high", "Grant 26 weeks paid maternity leave (first 2 children); 12 weeks for 3rd child and for adoption/surrogacy", "As required", "On employee request", "Labour Department", "Imprisonment up to 1 year + fine up to ₹5,000"
        A "Maternity Act", "high", "Provide crèche within 500m if 50+ employees; allow 4 nursing visits/day", "Permanent (50+ employees)", "Immediately on reaching 50 employees", "Labour Department", "Fine"
        A "Maternity Act", "high", "Display maternity benefit notice at workplace", "Permanent", "Always", "Labour Department", "Fine"
        A "Maternity Act", "high", "Offer work-from-home option after 26 weeks where nature of work permits (50+ employees)", "As requested", "On request after 26-week leave", "—", "Fine"
    End If

    If mTotalEmp > 0 Then
        L wsLaws, "high", "Employees' Compensation Act, 1923", "Social Security", "Applies to all employers with workers in specified occupations", 3, "Commissioner for Employees' Compensation"
        A "Comp Act", "high", "Pay compensation for work-related injury, occupational disease, or death", "As required", "Within 30 days of death; on settlement for injuries", "Commissioner for EC", "50% additional penalty + interest"
        A "Comp Act", "high", "Report fatal accidents to Commissioner within 7 days", "As required", "Within 7 days of fatality", "Commissioner for EC", "Fine"
        A "Comp Act", "high", "Maintain register of workers in scheduled occupations", "Ongoing", "At all times", "Labour Inspector", "Fine"
    End If

    ' ── B. LABOUR & EMPLOYMENT ───────────────────────────────────
    If mHasFactory And ((mFactPower And mFactoryW >= 10) Or (Not mFactPower And mFactoryW >= 20)) Then
        Dim r3 As String
        If mFactPower Then r3 = "Power-driven factory, " & mFactoryW & " workers (threshold 10)"
        Else r3 = "Non-power factory, " & mFactoryW & " workers (threshold 20)"
        L wsLaws, "critical", "Factories Act, 1948", "Labour", r3, 6, "Chief Inspector of Factories"
        A "Factories Act", "critical", "Obtain Factory Registration Certificate and Annual Licence (Form 4)", "One-time + Annual renewal", "Before commencing; renew before Dec 31 each year", "Chief Inspector of Factories (State)", "Imprisonment up to 2 years + fine up to ₹2 lakh"
        A "Factories Act", "critical", "Register Occupier; file Form 2 Notice of Occupation", "One-time", "Before registration", "Chief Inspector of Factories", "Fine"
        A "Factories Act", "critical", "Comply with health/welfare provisions: cleanliness, ventilation, lighting, drinking water, toilets, first aid", "Ongoing", "Always", "Factory Inspector", "Fine up to ₹2 lakh per violation"
        A "Factories Act", "critical", "Enforce working hours: max 9 hrs/day, 48 hrs/week; overtime at 2x wages", "Daily", "Always", "Factory Inspector", "Fine"
        A "Factories Act", "critical", "Grant earned leave: 1 day per 20 days worked (max 30 days carry-forward)", "Annual", "On worker request", "Factory Inspector", "Fine"
        A "Factories Act", "critical", "File annual return (Form 21) by 31 January", "Annual", "31st January", "Chief Inspector of Factories", "Fine"
    End If

    If mHasShop Or mTotalEmp > 0 Then
        L wsLaws, "critical", "Shops and Establishments Act (State-specific)", "Labour", "Applies to all shops/commercial establishments/offices in every state of operation", 4, "State Labour Department"
        A "Shops Act", "critical", "Register every establishment in each state of operation (within 30 days of opening)", "One-time per state + Annual renewal", "Within 30 days of opening", "Labour Department / Municipal Body (State)", "Fine up to ₹5,000 + ₹100/day (varies by state)"
        A "Shops Act", "critical", "Display registration certificate prominently at the establishment", "Permanent", "Immediately on registration", "Labour Inspector", "Fine"
        A "Shops Act", "critical", "Comply with working hours and weekly holiday as per state rules", "Daily", "Always", "Labour Inspector", "Fine"
        A "Shops Act", "critical", "File annual return (January 31 in most states)", "Annual", "31st January", "Labour Department", "Fine"
    End If

    If mTotalEmp > 0 Then
        L wsLaws, "critical", "Minimum Wages Act, 1948", "Labour", "Applies to all employers with workers in scheduled employments", 3, "Labour Commissioner"
        A "Min Wages Act", "critical", "Pay minimum wages as notified by State/Central Government for each category of worker", "Monthly", "Before 7th of following month", "Labour Commissioner", "Imprisonment up to 6 months + fine ₹500 per violation"
        A "Min Wages Act", "critical", "Display current minimum wage rates at workplace", "Permanent", "At all times", "Labour Inspector", "Fine"
        A "Min Wages Act", "critical", "File annual return (Form III) by 1st February", "Annual", "1st February", "Labour Commissioner", "Fine"
    End If

    If mTotalEmp > 0 Then
        L wsLaws, "high", "Payment of Wages Act, 1936", "Labour", "Applies to all establishments with employees", 2, "Labour Commissioner"
        A "Wages Act", "high", "Pay wages by 7th of following month (< 1000 employees) or 10th (1000+); no unauthorized deductions", "Monthly", "7th or 10th of following month", "Labour Commissioner", "Fine up to ₹7,500 per affected employee"
        A "Wages Act", "high", "Issue wage slips to every employee showing gross, deductions, and net wages", "Monthly", "On payment date", "Labour Inspector", "Fine"
    End If

    If mWomenEmp > 0 Or mTotalEmp >= 10 Then
        L wsLaws, "critical", "Prevention of Sexual Harassment at Workplace Act, 2013 (POSH)", "Labour", "Applies to all workplaces with women / 10+ employees", 4, "Labour Department / District Officer"
        A "POSH Act", "critical", "Constitute Internal Complaints Committee (ICC): woman presiding officer + 2 employees + 1 external NGO member; 50%+ women", "One-time (reconstitute every 3 years)", "Immediately", "Labour Department / District Officer", "Fine ₹50,000 first offence; ₹1 lakh repeat + business closure"
        A "POSH Act", "critical", "Publish written Anti-Sexual Harassment Policy and display ICC details at workplace", "Permanent", "Immediately", "Employer", "Fine"
        A "POSH Act", "critical", "Conduct POSH awareness training for all employees", "Annual", "Ongoing", "Employer", "Fine"
        A "POSH Act", "critical", "Submit Annual POSH Report to District Officer by 31st January", "Annual", "31st January", "District Officer / Labour Department", "Fine"
    End If

    If mContractW >= 20 Then
        L wsLaws, "high", "Contract Labour (Regulation and Abolition) Act, 1970", "Labour", "Contract workers = " & mContractW & " (threshold: 20)", 4, "Labour Commissioner"
        A "CLRA Act", "high", "Register as Principal Employer with Labour Commissioner (Form I)", "One-time", "Before engaging contract labour", "Labour Commissioner (Registering Officer)", "Fine"
        A "CLRA Act", "high", "Ensure every contractor obtains a Licence from Licensing Officer", "Per contractor", "Before work commences", "Labour Commissioner (Licensing Officer)", "Imprisonment + fine"
        A "CLRA Act", "high", "Ensure amenities for contract workers (rest rooms, water, first aid, canteen if applicable)", "Ongoing", "At all times", "Labour Inspector", "Fine (liability falls on principal employer if contractor defaults)"
        A "CLRA Act", "high", "File half-yearly return (Form VI-B) by 15 Feb and 15 Aug", "Half-yearly", "15th February and 15th August", "Labour Commissioner", "Fine"
    End If

    If mTotalEmp >= 1 Then
        L wsLaws, "high", "Industrial Disputes Act, 1947", "Labour", "Applies to all industrial establishments", 3, "Labour Commissioner / State Government"
        A "ID Act", "high", "Follow retrenchment procedure: 1 month notice or wages; govt permission needed for 100+ workers", "As required", "3 months prior (100+ workers); 1 month (others)", "State Government / Labour Commissioner", "Retrenchment void + reinstatement + back wages"
        A "ID Act", "high", "Constitute Works Committee if 100+ workers", "One-time (100+ workers)", "Within 30 days of reaching 100 workers", "Labour Department", "Fine"
        A "ID Act", "high", "Maintain notices and comply with standing orders provisions", "Ongoing", "Always", "Labour Inspector", "Fine"
    End If

    If mTotalEmp >= 100 Then
        L wsLaws, "medium", "Industrial Employment (Standing Orders) Act, 1946", "Labour", "Employees = " & mTotalEmp & " (threshold: 100)", 3, "Certifying Officer"
        A "Standing Orders", "medium", "Draft and get Standing Orders certified by Certifying Officer (Form B)", "One-time", "Within 6 months of reaching 100 workers", "Certifying Officer (Labour Commissioner)", "Fine ₹500 per day"
        A "Standing Orders", "medium", "Display certified standing orders in English + vernacular at main entrance and other places", "Permanent", "Immediately after certification", "Labour Department", "Fine"
        A "Standing Orders", "medium", "Renew / modify standing orders when business conditions change (Form C)", "As required", "On change in conditions", "Certifying Officer", "Fine"
    End If

    If mTotalEmp > 0 Then
        L wsLaws, "critical", "Child Labour (Prohibition and Regulation) Act, 1986", "Labour", "Absolute prohibition on employing children — applies to all employers", 2, "Labour Department / Police"
        A "Child Labour Act", "critical", "ABSOLUTE BAN: Do not employ any person below 14 years in any capacity", "Permanent", "Always", "Labour Department / Police", "Imprisonment 6 months–2 years + fine ₹20,000–₹50,000 (cognisable, non-bailable offence)"
        A "Child Labour Act", "critical", "Do not employ adolescents (14–18 years) in any hazardous process or occupation", "Permanent", "Always", "Labour Department", "Fine + imprisonment"
    End If

    If mWomenEmp > 0 And mTotalEmp > mWomenEmp Then
        L wsLaws, "medium", "Equal Remuneration Act, 1976", "Labour", "Employs both men and women employees", 2, "Labour Inspector"
        A "Equal Rem Act", "medium", "Ensure equal pay for men and women doing same or similar work — no gender-based discrimination in wages", "Ongoing", "Always", "Labour Inspector", "Fine up to ₹10,000 + imprisonment up to 1 month"
        A "Equal Rem Act", "medium", "Maintain register of workers showing male/female employees and wages paid (Form D)", "Ongoing", "At all times", "Labour Inspector", "Fine"
    End If

    If mMigrantW >= 5 Then
        L wsLaws, "medium", "Inter-State Migrant Workmen (Regulation) Act, 1979", "Labour", "Inter-state migrant workers = " & mMigrantW & " (threshold: 5)", 3, "Labour Commissioner"
        A "Migrant Act", "medium", "Register as Principal Employer; ensure contractor has licence in source and destination states", "One-time", "Before engaging migrant workers", "Labour Commissioner", "Imprisonment + fine"
        A "Migrant Act", "medium", "Provide displacement allowance (50% of monthly wages or ₹75 min) + journey allowance (to and fro)", "Per engagement", "Before journey", "Labour Inspector", "Fine"
        A "Migrant Act", "medium", "Provide suitable accommodation, medical facilities, and protective clothing at worksite", "Ongoing", "At all times", "Labour Inspector", "Fine"
    End If

    If mApprentices Or mIsManuf Then
        L wsLaws, "medium", "Apprentices Act, 1961", "Labour", "Applicable to establishments in specified industries (manufacturing, IT, etc.)", 3, "Directorate General of Training (DGT)"
        A "Apprentices Act", "medium", "Engage apprentices as per prescribed quota (2.5–10% of strength) — register on BOAT portal", "Annual", "As per DGT notification", "DGT / BOAT", "Fine ₹1,000 per quarter for shortfall"
        A "Apprentices Act", "medium", "Pay prescribed stipend monthly as per trade and year of apprenticeship", "Monthly", "On due date", "DGT", "Fine"
        A "Apprentices Act", "medium", "Register apprenticeship contracts with BOAT within 3 months of engagement", "Per apprentice", "Within 3 months of engagement", "BOAT / Regional Directorate", "Fine"
    End If

    If mConstruct And mTotalEmp >= 10 Then
        L wsLaws, "high", "Building and Other Construction Workers Act, 1996", "Labour", "Construction activities with " & mTotalEmp & " workers (threshold: 10)", 3, "State BOCW Welfare Board"
        A "BOCW Act", "high", "Register establishment with State BOCW Welfare Board within 60 days of commencement", "One-time", "Within 60 days of start", "State BOCW Welfare Board", "Fine"
        A "BOCW Act", "high", "Pay 1% BOCW Cess on cost of construction project", "Per project", "On commencement (assessed by municipal body)", "State Welfare Board / Municipal Authority", "Penalty + interest"
        A "BOCW Act", "high", "Provide mandatory safety equipment: helmets, harnesses, safety nets, first aid, fire extinguishers", "Ongoing", "Always at worksite", "BOCW Inspector", "Fine"
    End If

    If mPWDEmp > 0 Or mTotalEmp >= 20 Then
        L wsLaws, "medium", "Rights of Persons with Disabilities Act, 2016", "Labour", "Applicable: requires Equal Opportunity Policy for 20+ employee establishments", 3, "Chief Commissioner for PwD"
        A "RPwD Act", "medium", "Formulate and publish Equal Opportunity Policy for PwD employees (list reserved posts, facilities, liaison officer)", "One-time", "Within 1 year", "Chief Commissioner for PwD", "Fine up to ₹10,000"
        A "RPwD Act", "medium", "Register Equal Opportunity Policy with appropriate authority", "One-time", "Within 1 year", "Chief Commissioner for PwD", "Fine"
        A "RPwD Act", "medium", "Ensure accessible infrastructure (ramps, accessible washrooms, accessible pathways)", "Ongoing", "Progressive compliance", "District Magistrate", "Fine"
    End If

    ' ── C. TAX ──────────────────────────────────────────────────
    L wsLaws, "critical", "Income Tax Act, 1961", "Tax", "Applies to all entities — companies, LLPs, firms, and proprietorships", 6, "Income Tax Department"
    A "Income Tax", "critical", "Obtain PAN and quote it on all financial transactions", "One-time", "Before commencing business", "Income Tax Department", "₹10,000 penalty; 20% TDS without PAN"
    A "Income Tax", "critical", "Deduct TDS on salary (Sec 192), contractor (Sec 194C), rent (Sec 194I), professional fees (Sec 194J), etc.", "Monthly", "7th of following month (30 Apr for March)", "Income Tax Dept / TRACES", "1.5% per month + equal penalty to TDS amount"
    A "Income Tax", "critical", "File quarterly TDS Returns (Form 24Q for salary, 26Q for non-salary, 27Q for NRI)", "Quarterly", "31 Jul / 31 Oct / 31 Jan / 31 May", "TRACES Portal", "₹200/day late fee + fine equal to TDS"
    A "Income Tax", "critical", "Pay Advance Tax if liability > ₹10,000 (quarterly installments)", "Quarterly", "15 Jun (15%) / 15 Sep (45%) / 15 Dec (75%) / 15 Mar (100%)", "Income Tax Department", "Interest u/s 234B and 234C @ 1% per month"
    A "Income Tax", "critical", "File Annual Income Tax Return (ITR-6 for companies; ITR-5 for LLPs)", "Annual", "31 October (if tax audit); 31 July (others)", "Income Tax Department", "₹5,000 late fee + interest"
    A "Income Tax", "critical", "Tax Audit u/s 44AB if turnover > ₹1 Cr (business) or ₹50L (profession)", "Annual", "30th September", "Chartered Accountant + IT Dept", "0.5% of turnover or ₹1.5 lakh (lower) + interest"

    If mTurnover >= 20 Or mImportExp Or mIsEComm Then
        Dim r4 As String
        If mIsEComm Then r4 = "E-commerce: mandatory registration irrespective of turnover"
        ElseIf mImportExp Then r4 = "Import/Export business: mandatory GST registration"
        Else r4 = "Turnover ~" & TurnoverLabel(mTurnover) & " meets GST threshold"
        End If
        L wsLaws, "critical", "Goods and Services Tax (CGST / SGST / IGST) Acts, 2017", "Tax", r4, 6, "GST Portal (gst.gov.in)"
        A "GST", "critical", "Register on gst.gov.in; obtain GSTIN (separate registration in each state of operation)", "One-time per state", "Within 30 days of exceeding threshold", "GST Portal", "10% of tax due (min ₹10,000) or 100% if fraudulent"
        A "GST", "critical", "File GSTR-1 (outward supply details) — monthly or quarterly (QRMP)", "Monthly / Quarterly", "11th of following month (monthly); 13th (quarterly)", "GST Portal", "₹50/day (₹25 CGST + ₹25 SGST), max ₹5,000"
        A "GST", "critical", "File GSTR-3B (summary + tax payment) and pay net GST liability", "Monthly", "20th of following month (large taxpayers)", "GST Portal", "₹50/day + 18% p.a. interest on unpaid tax"
        A "GST", "critical", "File GSTR-9 Annual Return", "Annual", "31st December of following year", "GST Portal", "₹200/day max 0.25% of turnover"
        A "GST", "critical", "Issue GST-compliant invoices with GSTIN, HSN/SAC, tax breakup for all supplies", "Per transaction", "Before or at time of supply", "GST Portal / GST Officer", "₹10,000 or 100% of tax per invoice"
        A "GST", "critical", "Generate e-way bill for goods movement > ₹50,000 value", "Per consignment", "Before goods movement begins", "E-Way Bill Portal", "₹10,000 or tax evaded (higher) + detention"
    End If

    Dim ptStates As String
    ptStates = "maharashtra,karnataka,gujarat,west bengal,andhra pradesh,telangana,tamil nadu,madhya pradesh,assam,kerala,odisha,jharkhand,bihar,tripura,meghalaya,sikkim,manipur"
    Dim hasPT As Boolean: hasPT = False
    Dim ptList As String: ptList = ""
    Dim s As Variant
    For Each s In Split(ptStates, ",")
        If InStr(mStatesOp, Trim(s)) > 0 Then
            hasPT = True
            If ptList <> "" Then ptList = ptList & ", "
            ptList = ptList & Trim(s)
        End If
    Next s
    If mStatesOp = "" Then hasPT = True: ptList = "check applicable states"

    If hasPT Then
        L wsLaws, "medium", "Professional Tax (State-specific)", "Tax", "Applicable in states: " & ptList, 2, "State Commercial Tax / Labour Department"
        A "Professional Tax", "medium", "Register for Professional Tax in each applicable state; deduct from employee salary as per state slab", "Monthly / Annual (varies)", "As per state schedule (e.g., Maharashtra: 31 March)", "State PT Authority", "Penalty + interest (varies by state)"
        A "Professional Tax", "medium", "Pay employer's own Professional Tax on the profession", "Annual / Monthly", "As per state rules", "State PT Authority", "Penalty + interest"
    End If

    ' ── D. CORPORATE LAW ─────────────────────────────────────────
    If mEntityType = "Private Limited Company" Or mEntityType = "Public Limited Company" Or _
       mEntityType = "One Person Company (OPC)" Or mEntityType = "Section 8 Company" Or _
       mEntityType = "Government / PSU Company" Or InStr(LCase(mEntityType), "limited") > 0 Then
        L wsLaws, "critical", "Companies Act, 2013", "Corporate", "Applicable to all companies incorporated under Companies Act", 10, "Ministry of Corporate Affairs (ROC)"
        A "Companies Act", "critical", "Hold Annual General Meeting (AGM) within 6 months of FY end (by 30 September)", "Annual", "On or before 30th September", "MCA / ROC", "Fine up to ₹1 lakh + ₹5,000/day"
        A "Companies Act", "critical", "Hold minimum 4 Board Meetings per year (max gap 120 days between two)", "Quarterly", "Max 120-day gap", "ROC", "Fine on company (₹25,000) and directors (₹5,000)"
        A "Companies Act", "critical", "File Annual Return (MGT-7 or MGT-7A for small company) within 60 days of AGM", "Annual", "Within 60 days of AGM", "MCA (ROC)", "₹100/day"
        A "Companies Act", "critical", "File Financial Statements (AOC-4) within 30 days of AGM", "Annual", "Within 30 days of AGM", "MCA (ROC)", "₹100/day"
        A "Companies Act", "critical", "Complete Director KYC (DIR-3 KYC) for every director with active DIN", "Annual", "30th September", "MCA", "₹5,000 per director; DIN deactivated"
        A "Companies Act", "critical", "Statutory Audit by CA firm — obtain Auditor's Report before AGM", "Annual", "Before AGM", "Statutory Auditor (CA firm)", "Penal provisions under CA Act"
        A "Companies Act", "critical", "Maintain statutory registers: members, directors, charges, contracts (MGT-1, MBP-1, CHG-1, etc.)", "Ongoing", "At all times", "ROC", "Fine"
        A "Companies Act", "high", "CSR Compliance: spend 2% of average 3-year net profit if net worth ≥ ₹500 Cr OR turnover ≥ ₹1000 Cr OR net profit ≥ ₹5 Cr", "Annual", "31 March of following year", "MCA / ROC", "Fine ₹50,000–₹25 lakh + imprisonment up to 3 years for officers"
        A "Companies Act", "high", "Secretarial Audit (listed/public companies with large cap or turnover)", "Annual", "With Board Report", "Company Secretary in Practice", "Fine ₹1 lakh–₹5 lakh"
        A "Companies Act", "medium", "Appoint Internal Auditor (listed, unlisted public cos, private cos above thresholds)", "Annual", "As per Board decision", "CA / CMA (Internal Auditor)", "—"
    End If

    If InStr(LCase(mEntityType), "llp") > 0 Or mEntityType = "Limited Liability Partnership (LLP)" Then
        L wsLaws, "critical", "Limited Liability Partnership Act, 2008", "Corporate", "Applicable: entity is an LLP", 4, "MCA (ROC)"
        A "LLP Act", "critical", "File Annual Return (Form 11) by 30th May each year", "Annual", "30th May", "MCA (ROC)", "₹100/day"
        A "LLP Act", "critical", "File Statement of Accounts and Solvency (Form 8) by 30th October", "Annual", "30th October", "MCA (ROC)", "₹100/day"
        A "LLP Act", "critical", "Statutory Audit by CA if turnover > ₹40 lakh or contribution > ₹25 lakh", "Annual", "Before Form 8 filing", "Chartered Accountant", "Penal provisions"
        A "LLP Act", "critical", "Designated Partners' KYC (DPIN) annually by 30 September", "Annual", "30th September", "MCA", "DPIN deactivated + ₹5,000 penalty"
    End If

    If mIsListed Then
        L wsLaws, "critical", "SEBI (Listing Obligations and Disclosure Requirements) Regulations, 2015", "Corporate", "Company is listed on NSE / BSE", 6, "SEBI / Stock Exchange"
        A "SEBI LODR", "critical", "File quarterly financial results within 45 days of quarter end (60 days for Q4)", "Quarterly", "45 / 60 days from quarter end", "Stock Exchange (NSE/BSE)", "Fine + trading suspension"
        A "SEBI LODR", "critical", "File Corporate Governance Compliance Report (Reg 27) within 21 days of quarter end", "Quarterly", "21 days from quarter end", "Stock Exchange", "Fine ₹20,000–₹5 lakh per non-compliance"
        A "SEBI LODR", "critical", "Disclose material events / price-sensitive information to stock exchange immediately", "As required", "Within 24 hours of occurrence", "Stock Exchange / SEBI", "Fine + trading suspension"
        A "SEBI LODR", "critical", "Maintain minimum 25% public shareholding at all times", "Ongoing", "Always", "SEBI", "Suspension of trading"
        A "SEBI LODR", "critical", "Maintain minimum board composition: 1/3 independent directors (50% if exec chairman); 1 woman director", "Ongoing", "Always", "SEBI", "Fine up to ₹25 lakh per non-compliance"
        A "SEBI LODR", "critical", "File Annual Report and hold AGM within SEBI-prescribed timelines", "Annual", "30th September", "SEBI / ROC / Stock Exchange", "Fine"
    End If

    ' ── E. ENVIRONMENT ───────────────────────────────────────────
    If mHasFactory Or mMines Or mConstruct Or mHazWaste Or mPetroleum Then
        L wsLaws, "high", "Environment Protection Act, 1986", "Environment", "Industrial / construction / mining / hazardous operations", 3, "MoEFCC / State Pollution Control Board"
        A "EPA 1986", "high", "Obtain Environmental Clearance (EC) for specified project categories before commencement", "One-time per project", "Before commencement", "MoEFCC / SEIAA", "Imprisonment up to 5 years + fine up to ₹1 lakh/day"
        A "EPA 1986", "high", "Comply with Environmental Quality Standards (effluent, emission, noise, etc.)", "Ongoing", "Always", "SPCB / CPCB", "Imprisonment + fine + closure"
        A "EPA 1986", "high", "Submit Annual Environmental Compliance Report as per EC conditions", "Annual", "As per EC conditions", "MoEFCC / SPCB", "Fine"
    End If

    If mHasFactory Or mWaterDisc Or mHazWaste Then
        L wsLaws, "high", "Water (Prevention and Control of Pollution) Act, 1974", "Environment", "Industrial effluent discharge or hazardous waste operations", 4, "State Pollution Control Board (SPCB)"
        A "Water Act", "high", "Obtain Consent to Establish (CTE) from SPCB before setting up any water-polluting unit", "One-time", "Before establishing plant", "SPCB", "Imprisonment up to 6 years + fine"
        A "Water Act", "high", "Obtain Consent to Operate (CTO) and renew annually before expiry", "Annual renewal", "Before expiry of existing CTO", "SPCB", "Closure order + fine"
        A "Water Act", "high", "Install and operate Effluent Treatment Plant (ETP) meeting prescribed standards", "Ongoing", "Before receiving CTO", "SPCB", "Closure order + fine"
        A "Water Act", "high", "Submit monthly/quarterly effluent quality and quantity reports to SPCB", "Quarterly", "As per SPCB schedule", "SPCB", "Fine"
    End If

    If mHasFactory Or mAirEmit Or mMines Then
        L wsLaws, "high", "Air (Prevention and Control of Pollution) Act, 1981", "Environment", "Industrial air emission / dust generation", 3, "State Pollution Control Board (SPCB)"
        A "Air Act", "high", "Obtain Consent to Establish and Consent to Operate from SPCB; renew annually", "Annual renewal", "Before establishing / before renewal", "SPCB", "Imprisonment up to 6 years + fine"
        A "Air Act", "high", "Install adequate Air Pollution Control Equipment (scrubbers, ESP, dust collectors, etc.)", "Ongoing", "Before CTO", "SPCB", "Closure + fine"
        A "Air Act", "high", "Conduct stack emission monitoring and file quarterly reports", "Quarterly", "Submit reports quarterly", "SPCB", "Fine"
    End If

    If mHazWaste Or mChemicals Then
        L wsLaws, "high", "Hazardous and Other Wastes (Management) Rules, 2016", "Environment", "Generates or handles hazardous waste / chemicals", 3, "SPCB / CPCB"
        A "Haz Waste Rules", "high", "Obtain SPCB Authorization for hazardous waste handling (Form 1) — renew annually", "Annual renewal", "Before generating/storing hazardous waste", "SPCB", "Imprisonment up to 5 years + fine"
        A "Haz Waste Rules", "high", "Dispose hazardous waste only through SPCB-authorised TSDF agencies; use online manifests", "Per consignment", "No accumulation beyond limits", "SPCB / CPCB", "Fine + imprisonment"
        A "Haz Waste Rules", "high", "File Annual Hazardous Waste Return (Form 4) to SPCB by 30 June", "Annual", "30th June", "SPCB", "Fine"
    End If

    If mEWaste Or mIsIT Then
        L wsLaws, "medium", "E-Waste (Management) Rules, 2022", "Environment", "IT company or electronic equipment producer / user", 3, "CPCB"
        A "E-Waste Rules", "medium", "Register on CPCB E-Waste portal as Producer / Manufacturer", "One-time", "Before selling/distributing electronic equipment", "CPCB", "Fine + imprisonment"
        A "E-Waste Rules", "medium", "Meet EPR (Extended Producer Responsibility) collection and recycling targets", "Annual", "As per CPCB schedule", "CPCB", "Environmental Compensation"
        A "E-Waste Rules", "medium", "Dispose e-waste only through SPCB-authorised e-waste recyclers", "As required", "No stockpiling beyond limits", "SPCB / CPCB", "Fine"
    End If

    If mPlastic Or mIsManuf Or mFoodBev Then
        L wsLaws, "medium", "Plastic Waste Management Rules, 2016 (as amended)", "Environment", "Company uses plastic packaging / manufactures plastic products", 2, "CPCB / SPCB / Local Authority"
        A "Plastic Rules", "medium", "Stop use of all banned single-use plastic items (effective July 2022): cutlery, straws, plates, cups < 75 microns, polystyrene items", "Immediate", "Immediately", "CPCB / SPCB / Local Authority", "Fine up to ₹1 lakh + imprisonment"
        A "Plastic Rules", "medium", "Register under EPR for plastic packaging on CPCB portal; meet annual collection/recycling targets", "Annual", "Before selling packaged products", "CPCB", "Environmental Compensation"
    End If

    ' ── F. FOOD & HEALTH ─────────────────────────────────────────
    If mFoodBev Or mSector = "hospitality" Or mSector = "food" Then
        L wsLaws, "critical", "Food Safety and Standards Act, 2006 (FSSAI)", "Food & Health", "Company is engaged in food / beverage / hospitality business", 5, "FSSAI"
        A "FSSAI Act", "critical", "Obtain FSSAI Registration (turnover < ₹12 lakh) or State/Central Licence before commencing food business", "One-time + Annual renewal", "Before commencing", "FSSAI / State Food Safety Officer", "Imprisonment up to 6 months + fine up to ₹5 lakh"
        A "FSSAI Act", "critical", "Display 14-digit FSSAI licence number on premises and all food product labels", "Permanent", "Immediately", "FSSAI / Food Safety Officer", "Fine"
        A "FSSAI Act", "critical", "Comply with GMP and GHP standards (Schedule 4); maintain hygiene and food safety", "Ongoing", "Always", "FSSAI / State FSO", "Fine + cancellation of licence"
        A "FSSAI Act", "critical", "Ensure proper labelling: name, ingredients, nutrition, MFD/best before, net quantity, MRP", "Per product", "Before sale", "FSSAI / Legal Metrology", "Fine up to ₹3 lakh"
        A "FSSAI Act", "critical", "File Annual Return (Form D-1) — manufacturers only — by 31st May", "Annual", "31st May", "FSSAI / State Licensing Authority", "Fine"
    End If

    If mPharma Then
        L wsLaws, "critical", "Drugs and Cosmetics Act, 1940", "Food & Health", "Company deals in drugs, cosmetics, or healthcare products", 4, "CDSCO / State Drugs Controller"
        A "Drugs Act", "critical", "Obtain Drug Manufacturing Licence from State Licensing Authority / CDSCO (Form 25/28)", "One-time + Renewal", "Before manufacturing", "State Drugs Controller / CDSCO", "Imprisonment up to 3 years + fine"
        A "Drugs Act", "critical", "Obtain Drug Sale/Wholesale Licence (Form 20/21 retail; 20B/21B wholesale); appoint qualified pharmacist", "One-time + Annual", "Before selling drugs", "State Licensing Authority", "Imprisonment up to 2 years + fine"
        A "Drugs Act", "critical", "Maintain records of purchase and sale; special registers for Schedule H and H1 drugs", "Monthly", "At all times", "Drugs Inspector", "Fine"
        A "Drugs Act", "critical", "Ensure proper storage, temperature control, labelling (name, batch, expiry) of all drugs", "Ongoing", "Always", "Drugs Inspector", "Fine + imprisonment"
    End If

    ' ── G. IT & DATA ─────────────────────────────────────────────
    If mHasWeb Or mCollData Or mIsIT Or mIsEComm Or mHasPayment Then
        L wsLaws, "high", "Information Technology Act, 2000 & IT Amendment Act, 2008", "Technology & Data", "Company has digital presence or handles electronic data", 4, "MeitY / CERT-In"
        A "IT Act", "high", "Publish Privacy Policy on website/app disclosing data collection, purpose, sharing, and opt-out", "One-time + as updated", "Immediately", "MeitY", "Compensation payable to affected persons"
        A "IT Act", "high", "Implement reasonable security practices for Sensitive Personal Data (ISO 27001 or similar)", "Ongoing", "Always", "MeitY", "Compensation equal to loss caused"
        A "IT Act", "high", "Report cybersecurity incidents (data breach, ransomware, fraud) to CERT-In within 6 hours", "As required", "Within 6 hours of detection", "CERT-In", "Imprisonment + fine"
        A "IT Act", "high", "Appoint Grievance Officer; publish contact details; resolve user complaints within 15 days", "One-time", "Immediately", "MeitY", "Loss of safe harbour"
    End If

    If mCollData Or mHasWeb Or mIsIT Then
        L wsLaws, "critical", "Digital Personal Data Protection Act, 2023 (DPDP Act)", "Technology & Data", "Company collects or processes personal data of individuals", 4, "Data Protection Board of India"
        A "DPDP Act", "critical", "Obtain free, specific, informed, unambiguous consent before collecting/processing any personal data", "Per data principal", "Before processing", "Data Protection Board", "Up to ₹250 crore per violation"
        A "DPDP Act", "critical", "Publish clear Privacy Notice before/at time of data collection disclosing purpose and processing", "One-time + as updated", "Before data collection", "Data Protection Board", "Up to ₹200 crore"
        A "DPDP Act", "critical", "Implement data security safeguards — prevent breaches; notify Board and affected users if breach occurs", "Ongoing", "Always", "Data Protection Board", "Up to ₹250 crore"
        A "DPDP Act", "critical", "Fulfil Data Principal Rights: access, correction, erasure, grievance redressal within prescribed timelines", "On request", "Within prescribed timelines", "Data Protection Board", "Up to ₹150 crore"
    End If

    ' ── H. FINANCIAL ─────────────────────────────────────────────
    If mHasFDI Or mImportExp Or mHasForex Then
        L wsLaws, "high", "Foreign Exchange Management Act, 1999 (FEMA)", "Financial", "Company has FDI, imports/exports, or foreign exchange transactions", 5, "RBI / DGFT"
        A "FEMA", "high", "Report inward FDI to RBI within 30 days of share allotment (Form FC-GPR via AD bank)", "Per FDI transaction", "Within 30 days of allotment", "RBI (via Authorised Dealer bank)", "Up to 3x contravention amount or ₹2 lakh + ₹5,000/day"
        A "FEMA", "high", "File Annual Return on Foreign Liabilities and Assets (FLA) by 15 July", "Annual", "15th July", "RBI FEMA Division (XBRL portal)", "Fine + compounding"
        A "FEMA", "high", "Obtain IEC (Importer Exporter Code) from DGFT before first import/export; update annually", "One-time + Annual update", "Before first trade transaction", "DGFT", "Cannot import/export without IEC"
        A "FEMA", "high", "Realise export proceeds within 9 months of shipment; report to AD bank", "Per export", "Within 9 months", "RBI / AD Bank", "Fine proportional to unrealised amount"
        A "FEMA", "high", "File ODI returns for outward investments within 30 days of transaction", "Per ODI transaction", "Within 30 days", "RBI", "Fine + compounding"
    End If

    If mIsPMLA Or mNBFC Or mBanking Or mInsurance Then
        L wsLaws, "critical", "Prevention of Money Laundering Act, 2002 (PMLA)", "Financial", "Company is a reporting entity under PMLA", 4, "FIU-IND / RBI / SEBI / IRDAI"
        A "PMLA", "critical", "Implement KYC policy: Customer ID, UBO identification, risk categorisation, ongoing monitoring", "Ongoing", "Before onboarding any customer", "FIU-IND / Regulator", "Imprisonment up to 7 years + fine equal to proceeds"
        A "PMLA", "critical", "File Suspicious Transaction Reports (STR) to FIU-IND within 7 days of suspicion", "As required", "Within 7 days of suspicion arising", "FIU-IND (FINnet 2.0)", "Fine + imprisonment"
        A "PMLA", "critical", "File Cash Transaction Reports (CTR) for cash transactions > ₹10 lakh per month to FIU-IND by 15th", "Monthly", "15th of following month", "FIU-IND", "Fine + imprisonment"
        A "PMLA", "critical", "Maintain KYC and transaction records for minimum 5 years", "Ongoing", "At all times", "FIU-IND", "Fine"
    End If

    ' ── I. CONSUMER & TRADE ──────────────────────────────────────
    L wsLaws, "high", "Consumer Protection Act, 2019", "Consumer", "Applies to all businesses selling goods or services to consumers", 3, "Central Consumer Protection Authority (CCPA)"
    A "Consumer Protection", "high", "Avoid misleading advertisements, unfair trade practices, and false claims about products/services", "Ongoing", "Always", "CCPA / Consumer Courts", "Fine up to ₹10 lakh (first); ₹50 lakh (repeat) + imprisonment"
    A "Consumer Protection", "high", "Establish consumer grievance redressal mechanism; publish contact details prominently", "Ongoing", "Immediately", "CCPA", "Fine"
    A "Consumer Protection", "high", "E-commerce: display seller name, country of origin, return policy; no price manipulation (Consumer Protection (E-Commerce) Rules)", "Ongoing", "Always (e-commerce)", "CCPA / MCA", "Fine + imprisonment"

    If mIsManuf Or mIsTrading Or mFoodBev Or InStr(mSector, "retail") > 0 Then
        L wsLaws, "medium", "Legal Metrology Act, 2009", "Consumer", "Company manufactures or sells pre-packaged goods", 3, "Legal Metrology Inspector"
        A "Legal Metrology", "medium", "Declare MRP, net quantity, manufacturer name/address, manufacturing date, country of origin on all pre-packaged goods", "Per product", "Before sale", "Legal Metrology Inspector / State Dept of Weights & Measures", "Fine up to ₹25,000 + imprisonment"
        A "Legal Metrology", "medium", "Get all weighing/measuring instruments used in trade verified and stamped annually by Legal Metrology Inspector", "Annual", "Annual verification", "Legal Metrology Inspector", "Fine + confiscation"
        A "Legal Metrology", "medium", "E-commerce product listings must display all mandatory label declarations", "Ongoing", "Always", "Legal Metrology Inspector", "Fine"
    End If

    L wsLaws, "medium", "Competition Act, 2002", "Consumer", "Prohibitions on anti-competitive conduct apply to all enterprises; CCI merger notification above thresholds", 2, "Competition Commission of India (CCI)"
    A "Competition Act", "medium", "Avoid anti-competitive agreements with competitors: price fixing, market sharing, bid rigging, exclusive dealing", "Ongoing", "Always", "Competition Commission of India (CCI)", "Fine up to 10% of average 3-year turnover + imprisonment"
    A "Competition Act", "medium", "Do not abuse dominant market position: no predatory pricing, denial of market access, or tied selling", "Ongoing", "Always", "CCI", "Fine up to 10% of turnover + structural remedies"

    ' ── J. SECTOR-SPECIFIC ───────────────────────────────────────
    If mMines Then
        L wsLaws, "critical", "Mines Act, 1952", "Sector-Specific", "Company operates mines or quarries", 4, "Director General of Mines Safety (DGMS)"
        A "Mines Act", "critical", "Appoint Mine Manager with valid Certificate of Competency from DGMS before commencement", "One-time", "Before opening mine", "DGMS", "Imprisonment + fine; mine cannot operate"
        A "Mines Act", "critical", "Submit Mine Opening Notice and obtain DGMS permissions; file statistical returns quarterly", "One-time + Quarterly", "Before opening; quarterly thereafter", "DGMS Regional Inspector", "Closure order + fine"
        A "Mines Act", "critical", "Maintain ventilation, roof support, drainage, fire prevention systems as per DGMS regulations", "Ongoing", "Always", "DGMS Inspector", "Closure + imprisonment"
        A "Mines Act", "critical", "Report fatal/serious accidents by telephone immediately and in writing within 2 hours", "As required", "Immediately upon occurrence", "DGMS", "Fine"
    End If

    If mPetroleum Then
        L wsLaws, "critical", "Petroleum Act, 1934 and Petroleum Rules, 2002", "Sector-Specific", "Company stores or distributes petroleum products", 2, "PESO (Petroleum and Explosives Safety Organisation)"
        A "Petroleum Act", "critical", "Obtain Petroleum Storage Licence from PESO before storing above threshold quantities; renew annually", "Annual renewal", "Before storing; renew before expiry", "PESO", "Imprisonment up to 3 years + fine"
        A "Petroleum Act", "critical", "Comply with storage safety: fire prevention, grounding/bonding, safety distances, no-smoking zones, emergency procedures", "Ongoing", "Always", "PESO Inspector", "Fine + closure"
    End If

    If mBoilers Then
        L wsLaws, "high", "Indian Boilers Act, 1923", "Sector-Specific", "Company uses industrial steam boilers", 2, "State Boiler Inspector"
        A "Boilers Act", "high", "Register every boiler with State Boiler Inspectorate before use; obtain annual fitness certificate", "One-time + Annual", "Before use; annually before certificate expiry", "Chief Inspector of Boilers (State)", "Cannot operate; fine + imprisonment"
        A "Boilers Act", "high", "Employ only certified boiler attendants holding Certificate of Competency", "Ongoing", "Always", "State Boiler Inspector", "Fine"
    End If

    If mExplosives Then
        L wsLaws, "critical", "Explosives Act, 1884 and Explosives Rules, 2008", "Sector-Specific", "Company uses, manufactures, or stores explosives", 2, "PESO / Chief Controller of Explosives"
        A "Explosives Act", "critical", "Obtain Explosives Licence from PESO before storing/using explosives; renew annually", "Annual renewal", "Before any storage or use", "PESO", "Imprisonment up to 10 years + fine"
        A "Explosives Act", "critical", "Store in licensed magazines; maintain safety distances; ensure no unauthorised access; maintain daily registers", "Ongoing", "Always", "PESO Inspector", "Fine + imprisonment + licence cancellation"
    End If

    If mRealEstate Or InStr(mSector, "realestate") > 0 Then
        L wsLaws, "critical", "Real Estate (Regulation and Development) Act, 2016 (RERA)", "Sector-Specific", "Company is a real estate developer or agent", 4, "State Real Estate Regulatory Authority"
        A "RERA", "critical", "Register every real estate project (plot > 500 sq m or > 8 apartments) with State RERA before advertising/booking", "Per project", "Before any advertisement or booking", "State RERA Authority", "Fine up to 10% of project cost; imprisonment up to 3 years"
        A "RERA", "critical", "Open separate escrow bank account per project; deposit 70% of all collections for construction use only", "Per project", "Before receiving bookings", "State RERA", "Fine up to 10% of project cost"
        A "RERA", "critical", "File Quarterly Progress Reports (QPR) with State RERA within 15 days of quarter end", "Quarterly", "Within 15 days of quarter end", "State RERA", "Fine"
        A "RERA", "critical", "Real estate agents: register with State RERA before facilitating any transaction", "One-time + renewal", "Before facilitating any sale/purchase", "State RERA", "Fine up to ₹10,000/day"
    End If

    If mImportExp Then
        L wsLaws, "high", "Customs Act, 1962 and Foreign Trade Policy", "Sector-Specific", "Company imports or exports goods/services", 4, "Customs / DGFT"
        A "Customs Act", "high", "Obtain IEC (Importer Exporter Code) from DGFT; update annually on DGFT portal", "One-time + Annual update", "Before first trade", "DGFT", "Cannot import/export without IEC"
        A "Customs Act", "high", "File Bill of Entry on ICEGATE for every import consignment; pay customs duty and IGST before clearance", "Per import", "Before clearance of goods", "Customs Department (ICEGATE)", "Demurrage + penalty + detention"
        A "Customs Act", "high", "File Shipping Bill on ICEGATE for every export; obtain Let Export Order (LEO)", "Per export", "Before shipment", "Customs Department", "Penalty"
        A "Customs Act", "high", "Claim export benefits (RoDTEP, etc.) within 1 year of export", "Per export", "Within 1 year of export date", "DGFT", "Benefit forfeited if not claimed"
    End If

    If mLargeElec Or mHasFactory Or mMines Then
        L wsLaws, "medium", "Electricity Act, 2003 and Energy Conservation Act", "Infrastructure", "Company has large electrical installation or industrial operations", 3, "Bureau of Energy Efficiency (BEE) / State Electrical Inspector"
        A "Electricity Act", "medium", "Ensure all electrical work is carried out by licensed electrical contractors only", "Ongoing", "Always", "State Electrical Inspectorate", "Fine + imprisonment"
        A "Electricity Act", "medium", "Conduct Energy Audit every 3 years if Designated Consumer (> 500 TOE/year or > 30,000 units/month)", "Every 3 years", "As per BEE notification", "BEE / State Designated Agency", "Fine up to ₹10 lakh"
        A "Electricity Act", "medium", "Appoint certified Energy Manager and file Annual Energy Consumption Return by 30 September", "Annual", "30th September", "BEE", "Fine"
    End If

    ' ── K. IPR ───────────────────────────────────────────────────
    If mHasIP Or mTotalEmp > 0 Then
        L wsLaws, "medium", "Trade Marks Act, 1999", "Intellectual Property", "Company should protect its brand name, logo, and tagline", 3, "Trade Marks Registry / IP India"
        A "Trade Marks Act", "medium", "Conduct trademark search on IP India database before adopting any new brand name or logo", "One-time", "Before use of mark", "IP India (CGPDTM)", "N/A — preventive step"
        A "Trade Marks Act", "medium", "File trademark application (Form TM-A) on IP India portal for brand name, logo, tagline", "Per mark", "As early as possible", "Trade Marks Registry", "No penalty for not registering but risk of infringement by others"
        A "Trade Marks Act", "medium", "Renew registered trademark every 10 years (Form TM-R)", "Every 10 years", "Before expiry", "Trade Marks Registry", "Removal from register after 1 year"
    End If

    If mIsIT Or InStr(mSector, "media") > 0 Or mHasIP Then
        L wsLaws, "low", "Copyright Act, 1957", "Intellectual Property", "Company creates software, content, designs, or copyrightable works", 2, "Copyright Office / DPIIT"
        A "Copyright Act", "low", "Include IP assignment clause in all employee and contractor agreements (copyright vests with employer)", "One-time per hire", "At time of engagement", "—", "Employer may not own created works without explicit assignment"
        A "Copyright Act", "low", "Obtain licences for all third-party copyrighted material: software, stock images, fonts, music", "Before use", "Before deploying in any product or marketing", "—", "Civil and criminal action by copyright owner"
    End If

    ' ── L. LABOUR WELFARE FUND ───────────────────────────────────
    Dim lwfStates As String
    lwfStates = "andhra,telangana,chandigarh,delhi,goa,gujarat,haryana,karnataka,kerala,madhya pradesh,maharashtra,odisha,orissa,punjab,tamil,uttarakhand,west bengal"
    Dim hasLWF As Boolean: hasLWF = False
    Dim lwfList As String: lwfList = ""
    For Each s In Split(lwfStates, ",")
        If InStr(mStatesOp, Trim(s)) > 0 Then
            hasLWF = True
            If lwfList <> "" Then lwfList = lwfList & ", "
            lwfList = lwfList & Trim(s)
        End If
    Next s
    If mStatesOp = "" Then hasLWF = True: lwfList = "check applicable states"

    If hasLWF And mTotalEmp > 0 Then
        L wsLaws, "medium", "Labour Welfare Fund Act (State-specific)", "Labour", "Applicable in: " & lwfList, 2, "State Labour Welfare Board"
        A "LWF Act", "medium", "Deduct and deposit LWF contributions (e.g., Maharashtra: Employee ₹6, Employer ₹18 per 6 months)", "Half-yearly", "31st January and 31st July", "State Labour Welfare Board", "Fine (varies by state)"
        A "LWF Act", "medium", "File Labour Welfare Fund half-yearly / annual returns", "Half-yearly or Annual", "As per state rules", "State Labour Welfare Board", "Fine"
    End If

    ' Update dashboard stats
    UpdateDashboardStats
End Sub

' ================================================================
'  HELPER: Write Law Row
' ================================================================
Private Sub L(ws As Worksheet, priority As String, lawName As String, _
              cat As String, whyApplies As String, actCount As Long, auth As String)
    Dim r As Long: r = rLaws
    Dim fg As Long, bg As Long, badge As String
    GetColors priority, fg, bg, badge

    With ws
        .Cells(r, 1).Value = rLaws - 3
        .Cells(r, 2).Value = badge & " " & UCase(priority)
        .Cells(r, 3).Value = lawName
        .Cells(r, 4).Value = cat
        .Cells(r, 5).Value = whyApplies
        .Cells(r, 6).Value = actCount
        .Cells(r, 7).Value = auth

        Dim c As Integer
        For c = 1 To 7
            With .Cells(r, c)
                .Interior.Color = bg
                .Font.Color = fg
                .WrapText = True
                .VerticalAlignment = xlTop
                .RowHeight = 32
                If c = 2 Then .Font.Bold = True
                If c = 3 Then .Font.Bold = True
            End With
        Next c
        .Cells(r, 2).Interior.Color = GetBadgeColor(priority)
        .Cells(r, 2).Font.Color = C_WHITE
    End With
    rLaws = rLaws + 1
End Sub

' ================================================================
'  HELPER: Write Action Row
' ================================================================
Private Sub A(lawName As String, priority As String, title As String, _
              freq As String, deadline As String, auth As String, penalty As String)
    Dim fg As Long, bg As Long, badge As String
    GetColors priority, fg, bg, badge

    ' ── Checklist ──
    With wsCheck
        .Cells(rCheck, 1).Value = rSr
        .Cells(rCheck, 2).Value = badge & " " & UCase(priority)
        .Cells(rCheck, 3).Value = lawName
        .Cells(rCheck, 4).Value = GetCat(lawName)
        .Cells(rCheck, 5).Value = title
        .Cells(rCheck, 6).Value = freq
        .Cells(rCheck, 7).Value = deadline
        .Cells(rCheck, 8).Value = auth
        .Cells(rCheck, 9).Value = penalty
        .Cells(rCheck, 10).Value = Chr(9744) & " Pending"

        Dim c As Integer
        For c = 1 To 10
            With .Cells(rCheck, c)
                .Interior.Color = bg
                .Font.Color = fg
                .WrapText = True
                .VerticalAlignment = xlTop
                .RowHeight = 36
            End With
        Next c
        .Cells(rCheck, 2).Interior.Color = GetBadgeColor(priority)
        .Cells(rCheck, 2).Font.Color = C_WHITE
        .Cells(rCheck, 2).Font.Bold = True
        .Cells(rCheck, 5).Font.Bold = True
        .Cells(rCheck, 7).Font.Color = RGB(6, 95, 70)
        .Cells(rCheck, 9).Font.Color = RGB(153, 27, 27)
    End With
    rCheck = rCheck + 1

    ' ── Calendar ──
    Dim bucket As String: bucket = FreqBucket(freq)
    WriteCalendarRow bucket, priority, lawName, title, deadline, auth, penalty

    ' ── Urgent ──
    If priority = "critical" Or priority = "high" Then
        With wsUrgent
            .Cells(rUrgent, 1).Value = badge & " " & UCase(priority)
            .Cells(rUrgent, 2).Value = lawName
            .Cells(rUrgent, 3).Value = title
            .Cells(rUrgent, 4).Value = deadline
            .Cells(rUrgent, 5).Value = penalty
            .Cells(rUrgent, 6).Value = auth
            .Cells(rUrgent, 7).Value = Chr(9744)

            For c = 1 To 7
                With .Cells(rUrgent, c)
                    .Interior.Color = bg
                    .Font.Color = fg
                    .WrapText = True
                    .VerticalAlignment = xlTop
                    .RowHeight = 36
                End With
            Next c
            .Cells(rUrgent, 1).Interior.Color = GetBadgeColor(priority)
            .Cells(rUrgent, 1).Font.Color = C_WHITE
            .Cells(rUrgent, 1).Font.Bold = True
            .Cells(rUrgent, 3).Font.Bold = True
            .Cells(rUrgent, 4).Font.Color = RGB(6, 95, 70)
            .Cells(rUrgent, 5).Font.Color = RGB(153, 27, 27)
        End With
        rUrgent = rUrgent + 1
    End If

    rSr = rSr + 1
End Sub

' ── Calendar row writer ──
Private Sub WriteCalendarRow(bucket As String, priority As String, lawName As String, _
                              title As String, deadline As String, auth As String, penalty As String)
    Static lastBucket As String
    Dim fg As Long, bg As Long, badge As String
    GetColors priority, fg, bg, badge

    If bucket <> lastBucket Then
        If rCal > 4 Then rCal = rCal + 1
        Dim bucketLabel As String, bucketColor As Long
        Select Case bucket
            Case "One-time":    bucketLabel = Chr(9671) & " ONE-TIME SETUP":        bucketColor = RGB(124, 58, 237)
            Case "Monthly":     bucketLabel = Chr(128308) & " MONTHLY (Recurring)": bucketColor = RGB(220, 38, 38)
            Case "Quarterly":   bucketLabel = Chr(128992) & " QUARTERLY":           bucketColor = RGB(217, 119, 6)
            Case "Half-yearly": bucketLabel = Chr(128995) & " HALF-YEARLY":         bucketColor = RGB(190, 24, 93)
            Case "Annual":      bucketLabel = Chr(128994) & " ANNUAL":              bucketColor = RGB(5, 150, 105)
            Case Else:          bucketLabel = Chr(128309) & " AS REQUIRED / ONGOING": bucketColor = RGB(8, 145, 178)
        End Select
        With wsCal
            .Range(.Cells(rCal, 1), .Cells(rCal, 6)).Merge
            .Cells(rCal, 1).Value = bucketLabel
            .Cells(rCal, 1).Interior.Color = bucketColor
            .Cells(rCal, 1).Font.Color = C_WHITE
            .Cells(rCal, 1).Font.Bold = True
            .Cells(rCal, 1).Font.Size = 10
            .Cells(rCal, 1).RowHeight = 22
        End With
        rCal = rCal + 1
        Call ColHdr(wsCal, rCal, Array("Priority", "Law Name", "Action Required", "Deadline", "Authority", "Penalty"))
        rCal = rCal + 1
        lastBucket = bucket
    End If

    With wsCal
        .Cells(rCal, 1).Value = badge & " " & UCase(priority)
        .Cells(rCal, 2).Value = lawName
        .Cells(rCal, 3).Value = title
        .Cells(rCal, 4).Value = deadline
        .Cells(rCal, 5).Value = auth
        .Cells(rCal, 6).Value = penalty
        Dim c As Integer
        For c = 1 To 6
            With .Cells(rCal, c)
                .Interior.Color = bg
                .Font.Color = fg
                .WrapText = True
                .VerticalAlignment = xlTop
                .RowHeight = 32
            End With
        Next c
        .Cells(rCal, 1).Interior.Color = GetBadgeColor(priority)
        .Cells(rCal, 1).Font.Color = C_WHITE
        .Cells(rCal, 1).Font.Bold = True
        .Cells(rCal, 3).Font.Bold = True
        .Cells(rCal, 4).Font.Color = RGB(6, 95, 70)
        .Cells(rCal, 6).Font.Color = RGB(153, 27, 27)
    End With
    rCal = rCal + 1
End Sub

' ================================================================
'  HELPERS
' ================================================================
Private Sub GetColors(priority As String, ByRef fg As Long, ByRef bg As Long, ByRef badge As String)
    Select Case LCase(priority)
        Case "critical": fg = C_CRIT_FG: bg = RGB(254, 226, 226): badge = Chr(128308)
        Case "high":     fg = C_HIGH_FG: bg = RGB(254, 243, 199): badge = Chr(128992)
        Case "medium":   fg = C_MED_FG:  bg = RGB(224, 242, 254): badge = Chr(128309)
        Case Else:       fg = C_LOW_FG:  bg = RGB(209, 250, 229): badge = Chr(128994)
    End Select
End Sub

Private Function GetBadgeColor(priority As String) As Long
    Select Case LCase(priority)
        Case "critical": GetBadgeColor = C_CRIT_FG
        Case "high":     GetBadgeColor = C_HIGH_FG
        Case "medium":   GetBadgeColor = C_MED_FG
        Case Else:       GetBadgeColor = C_LOW_FG
    End Select
End Function

Private Function FreqBucket(freq As String) As String
    Dim f As String: f = LCase(freq)
    If InStr(f, "one-time") > 0 Or InStr(f, "one time") > 0 Or InStr(f, "per ") > 0 Then
        FreqBucket = "One-time"
    ElseIf InStr(f, "month") > 0 Then
        FreqBucket = "Monthly"
    ElseIf InStr(f, "quarter") > 0 Then
        FreqBucket = "Quarterly"
    ElseIf InStr(f, "half") > 0 Or InStr(f, "6 month") > 0 Then
        FreqBucket = "Half-yearly"
    ElseIf InStr(f, "annual") > 0 Or InStr(f, "year") > 0 Or InStr(f, "10 year") > 0 Or InStr(f, "3 year") > 0 Then
        FreqBucket = "Annual"
    Else
        FreqBucket = "As required"
    End If
End Function

Private Function GetCat(lawName As String) As String
    Dim n As String: n = LCase(lawName)
    If InStr(n, "epf") > 0 Or InStr(n, "esi") > 0 Or InStr(n, "gratuity") > 0 Or InStr(n, "comp act") > 0 Then GetCat = "Social Security"
    ElseIf InStr(n, "tax") > 0 Or InStr(n, "gst") > 0 Or InStr(n, "income") > 0 Or InStr(n, "professional") > 0 Then GetCat = "Tax"
    ElseIf InStr(n, "companies") > 0 Or InStr(n, "llp") > 0 Or InStr(n, "sebi") > 0 Then GetCat = "Corporate"
    ElseIf InStr(n, "water") > 0 Or InStr(n, "air") > 0 Or InStr(n, "haz") > 0 Or InStr(n, "plastic") > 0 Or InStr(n, "e-waste") > 0 Or InStr(n, "epa") > 0 Then GetCat = "Environment"
    ElseIf InStr(n, "fssai") > 0 Or InStr(n, "drug") > 0 Then GetCat = "Food & Health"
    ElseIf InStr(n, "it act") > 0 Or InStr(n, "dpdp") > 0 Then GetCat = "Technology & Data"
    ElseIf InStr(n, "fema") > 0 Or InStr(n, "pmla") > 0 Then GetCat = "Financial"
    ElseIf InStr(n, "consumer") > 0 Or InStr(n, "metrology") > 0 Or InStr(n, "competition") > 0 Then GetCat = "Consumer"
    ElseIf InStr(n, "trade mark") > 0 Or InStr(n, "copyright") > 0 Or InStr(n, "patent") > 0 Then GetCat = "IPR"
    Else: GetCat = "Labour"
    End If
End Function

Private Sub UpdateDashboardStats()
    Dim totalLaws As Long: totalLaws = rLaws - 4
    Dim totalActs As Long: totalActs = rSr - 1

    With wsDash
        .Range("A12").Value = "Total Laws Applicable"
        .Range("B12").Value = totalLaws
        .Range("B12").Font.Bold = True
        .Range("B12").Font.Size = 14
        .Range("B12").Font.Color = C_GOLD

        .Range("A13").Value = "Total Compliance Actions"
        .Range("B13").Value = totalActs
        .Range("B13").Font.Bold = True

        .Range("A14").Value = "Urgent Actions (Critical/High)"
        .Range("B14").Value = rUrgent - 4
        .Range("B14").Font.Color = C_CRIT_FG
        .Range("B14").Font.Bold = True

        .Range("A16").Value = "NEXT STEPS"
        .Range("A16").Font.Bold = True
        .Range("A16").Font.Color = C_BLUE
        .Range("B16").Value = "1. Review 'Urgent Actions' tab immediately"
        .Range("B17").Value = "2. Use 'Compliance Checklist' tab for tracking (tick off completed items)"
        .Range("B18").Value = "3. Use 'Compliance Calendar' tab to schedule recurring tasks"
        .Range("B19").Value = "4. Consult a qualified CA / CS / Advocate for each law before acting"
        .Range("B20").Value = "DISCLAIMER: This report is for informational purposes only and does not constitute legal advice."
        .Range("B20").Font.Italic = True
        .Range("B20").Font.Color = C_DGRAY
    End With
End Sub
