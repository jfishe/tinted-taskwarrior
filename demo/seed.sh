#!/bin/sh
# Rebuild the demo task database so every tinted-taskwarrior color rule has
# something to show: priorities, projects, tags, due/overdue/today, scheduled,
# active, blocked/blocking, recurring, waiting, completed and deleted tasks,
# plus a few weeks of history for burndown/history/summary.
#
# Dates are relative, so the demo always looks current. Never touches
# ~/.taskrc or ~/.task; see demo/lib.sh.
set -eu
# shellcheck source=demo/lib.sh
. "$(dirname -- "$0")/lib.sh"

rm -rf "$TASKDATA"
mkdir -p "$TASKDATA"

t() { task rc.verbose=new-id "$@" 2>/dev/null; }
# Add a task and print its ID.
add() { t add "$@" | sed -n 's/^Created task \([0-9][0-9]*\).*/\1/p'; }

# History: tasks created over the last few weeks, some finished, one deleted.
t log "Renew passport" project:Home entry:now-5wk end:now-4wk >/dev/null
t log "Order seeds" project:Garden entry:now-4wk end:now-3wk >/dev/null
t log "Set up CI pipeline" project:Work.Website +devops entry:now-4wk end:now-17d >/dev/null
t log "Write release notes draft" project:Work.Release entry:now-3wk end:now-12d >/dev/null
t log "Fix login redirect" project:Work.Website +bug entry:now-3wk end:now-8d >/dev/null
t log "Clean the gutters" project:Home entry:now-2wk end:now-5d >/dev/null
t log "Mulch the beds" project:Garden entry:now-12d end:now-2d >/dev/null
t log "Review pull requests" project:Work.Website entry:now-1wk end:now-1d >/dev/null

# Pending work.
add "Pay the electricity bill" project:Home priority:H due:yesterday +bills entry:now-2wk >/dev/null
add "File expense report" project:Work priority:M due:now-3d entry:now-3wk >/dev/null
add "Call the plumber" project:Home due:today priority:H entry:now-4d >/dev/null
add "Plant tomatoes" project:Garden due:tomorrow scheduled:today entry:now-10d >/dev/null
add "Prune the roses" project:Garden due:eow priority:L entry:now-6d >/dev/null

design=$(add "Design new landing page" project:Work.Website priority:H +next due:eow entry:now-2wk)
migrate=$(add "Migrate blog to static site" project:Work.Website priority:M entry:now-16d)
add "Write deployment checklist" project:Work.Website depends:"$migrate" entry:now-1wk >/dev/null
add "Launch new landing page" project:Work.Website depends:"$design" due:now+10d entry:now-1wk >/dev/null

t "$design" start >/dev/null
t "$design" annotate "Mockups in the shared drive" >/dev/null

tag=$(add "Tag v2.0 release" project:Work.Release priority:H +next due:now+5d entry:now-9d)
t "$tag" annotate "Waiting on QA sign-off" >/dev/null
add "Fix crash on empty config" project:Work.Release +bug priority:H entry:now-3d >/dev/null
add "Update changelog" project:Work.Release scheduled:now+2d priority:L entry:now-2d >/dev/null

add "Water the plants" project:Garden recur:weekly due:now+1d entry:now-3wk >/dev/null
add "Take out recycling" project:Home recur:weekly due:now+3d priority:L entry:now-4wk >/dev/null
add "Buy birthday present" project:Home wait:now+3d due:now+2wk >/dev/null
add "Read 'Getting Things Done'" +someday entry:now-1wk >/dev/null
add "Return library books" until:now+5d due:now+4d entry:now-5d >/dev/null
add "Learn Rust" priority:L entry:now-4wk >/dev/null

# Removed and finished today, so burndown shows today's progress too.
gone=$(add "Repaint the shed" project:Garden entry:now-3wk)
t "$gone" delete >/dev/null
done_today=$(add "Book dentist appointment" project:Home priority:M entry:now-6d)
t "$done_today" "done" >/dev/null

# Generate recurring instances now rather than on the first report.
task rc.verbose=nothing list >/dev/null 2>&1 || true

echo "Seeded $(task rc.verbose=nothing count status:pending) pending tasks in $TASKDATA"
