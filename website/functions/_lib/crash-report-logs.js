// The log names a crash report may carry, in the order they are shown: in the
// GitHub issue, on the admin page, and when the service keeps a report's logs.
// The endpoint and the admin page both read this list so they can't drift apart.
// The problems log comes first: it holds the game's warnings and errors, and it is
// the reason a clean-exit report is sent at all.
export const LOG_ORDER = [
    "native_problems",
    "native_crash",
    "native_run",
    "native_stderr",
    "launcher",
    "native_stdout",
];

export const LOG_LABELS = {
    native_problems: "Game problems (mw3-problems.log)",
    native_crash: "Native crash details (crash.txt)",
    native_run: "Native run log (mw3.log)",
    native_stderr: "Native standard error",
    launcher: "Launcher log",
    native_stdout: "Native standard output",
};
