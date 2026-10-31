# discovery search loses typed characters during url navigation

status: source fix awaiting an isolated rebuild and actual native browser verification. no green browser result is claimed.

root typed `toffoli` once through native cua on the final fixture03 build. the url became `q=tfoi`; the input displayed `ofl`. the controlled input read committed url state while `flushSync: true` exposed the pending navigation first, restoring the previous value during typing. this can corrupt ordinary name filtering.

the narrow fix reads the input value from the existing pending-or-current `viewSearch` owner. clearing filters also drops its stale committed-value early return; the existing commit comparison handles no-op updates. url keys, replacement history, deep links and filtering semantics remain unchanged. player picker and numeric drafts already keep their immediate input locally and do not share this boundary.

resolution requires the rebuilt isolated fixture candidate to preserve literal `toffoli` in input and url through ordinary typing and paste, show the matching player, clear correctly and retain direct-link/back behavior. root controls native browser actions. stop owned server `26820` before changing its built files; leave the primary live application untouched.
