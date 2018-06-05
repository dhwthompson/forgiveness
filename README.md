# Forgiveness

This is a quick and somewhat cobbled-together script that perpetually tweaks
due dates on Wunderlist tasks, so they never come up as overdue. I've done
this as an alternative to tasks that recur from their due dates, as Wunderlist
doesn't support this natively. Also, for recurring tasks, having a list of
overdue tasks isn't as motivating as having a list of tasks that I could do
today.

I'm running this on Heroku, through the scheduler add-on. It seems to work
well enough for my purposes, and it's hard to argue with "free" as an
operating cost.

## Tasty caveats

If you particularly want to use this for your own stuff, I'm not going to
stop you, but I make no promises that this will keep working, or that it won't
somehow break your data, or start deleting things, or other horrible stuff.
