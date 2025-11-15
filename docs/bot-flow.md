```mermaid
flowchart LR
    start[/User triggers /start or deeplink/]
    greet["Send texts.greet + start keyboard"]
    accept{{start_accept callback}}
    profileFSM["Collect profile\nUpdate_user_info.*"]
    menu[[texts.menu\n(main menu keyboard)]]

    start --> greet --> accept
    accept -->|profile found| menu
    accept -->|profile missing| profileFSM --> menu

    menu --> support["support callback\nstate: get_prompt.helper_prompt"]
    menu --> soulsleep["soulsleep callback\nstate: get_prompt.soulsleep_prompt"]
    menu --> analysisMenu["analysis callback\nanalysis_menu keyboard"]
    menu --> mediaRoot["media_categories {type}"]
    menu --> profileMenu["profile callback\nprofile_menu"]
    menu --> quizEntry["quiz_start callback or /quiz command"]
    menu --> settingsCmd["/settings command"]
    menu --> webapp["/webapp command\nwebapp_info/back"]
    menu --> deleteContext["/deletecontext command"]
    menu --> menuCmd["/menu command"]

    support --> helperChat["helper assistant chat"]
    soulsleep --> sleeperChat["soulsleep assistant chat"]
    helperChat --> menu
    sleeperChat --> menu

    deleteContext --> support
    menuCmd --> menu
    settingsCmd --> styleSettings

    analysisMenu --> relPrompt["relationships preview"]
    analysisMenu --> moneyPrompt["money preview"]
    analysisMenu --> confidencePrompt["confidence preview"]
    relPrompt -- "▶️ Начать" --> quizRunning
    moneyPrompt -- "▶️ Начать" --> quizRunning
    confidencePrompt -- "▶️ Начать" --> quizRunning
    relPrompt -- "↩️ Назад" --> analysisMenu
    moneyPrompt -- "↩️ Назад" --> analysisMenu
    confidencePrompt -- "↩️ Назад" --> analysisMenu

    mediaRoot --> mediaCategory["media_category {id}"]
    mediaCategory --> mediaFile["media_file {id}"]
    mediaFile --> mediaCategory
    mediaRoot --> sounds["sounds playlist"]
    sounds --> mediaRoot
    mediaCategory --> menu
    mediaRoot --> menu

    profileMenu --> viewProfile["view_psychological_profile"]
    profileMenu --> updateProfile["update_user_info FSM"]
    profileMenu --> styleSettings["style_settings / style_*"]
    profileMenu --> stylePresets["style_presets / preset_*"]
    profileMenu --> premium["premium → pay → check_pay"]
    profileMenu --> profileMenuBack["↩️ button (menu)"]
    viewProfile --> menu
    updateProfile --> menu
    styleSettings --> profileMenu
    stylePresets --> profileMenu
    premium --> menu
    profileMenuBack --> menu

    quizEntry --> resumeQuiz["quiz_resume"]
    quizEntry --> newQuiz["quiz_new"]
    quizEntry --> quizCategories["quiz_category_*"]
    quizEntry --> quizIntro["Deeplink intro message\n(«Нажми Начать» экран)"]
    resumeQuiz --> quizRunning
    newQuiz --> quizCategories
    quizCategories --> quizRunning
    quizCategories -->|🏠 Меню| menu
    quizRunning(("FSM: QuizStates.waiting_for_answer"))
    quizRunning --> quizRunning
    quizRunning -->|/menu или /start| menu
    quizRunning --> quizResults["Quiz results shown"]
    quizIntro -->|▶️ Начать| quizRunning
    quizIntro -->|🏠 Меню| menu
    quizResults --> quizComplete["Flow end"]
    quizResults -->|нет подписки| paywall["Плашка подписки (sub_menu)"]
    paywall --> menu

    webapp --> menu
```

