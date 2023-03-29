# task-chan
## What's this?
Task-chan is a discord reminder bot which can talk with!
It use gpt-3.5-turbo and we can have a brief chat!

## commands
### add-task
Add your task to task-list.
```
/add-task due  description  y/m/d h:d  point
```
We can set a "point" and it will increase the task-chan's likeability.

### show-tasks
Show all of your tasks.

### talk
Talk with task-chan!
```
/talk text
```

### save
Save all tasks so as not to lose them.

### load
Load task-list and user-list. That's enables this bot to recall tasks after rebooting.

## Points to be fixed
- There are some bugs in "save" and "load"
  - pickle error
- Reminder function isn't implemented (what is a reminder bot?🤔)
