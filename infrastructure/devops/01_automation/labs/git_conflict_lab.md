# DevOps Guided Lab: Git Merge Conflicts

In DevOps, you will frequently collaborate with other engineers. This lab simulates a scenario where two developers edit the same file simultaneously, causing a merge conflict. We will learn how to resolve it safely.

## Step 1: Set up the scenario

First, let's create a fresh git repository to play in. Run these commands in your terminal:

```bash
# Create a new directory and initialize git
mkdir git-lab && cd git-lab
git init

# Create our base application file
echo 'print("Hello from the main branch!")' > app.py
git add app.py
git commit -m "Initial commit on main"
```

## Step 2: Create a Feature Branch

You are assigned to work on a new feature. You create a branch and make changes.

```bash
git checkout -b feature/new-greeting
echo 'print("Hello from the AWESOME new feature!")' > app.py
git commit -am "Update greeting in feature branch"
```

## Step 3: Simulate a Teammate's Conflicting Change

While you were working, your teammate pushed a change directly to `main` modifying the *exact same line*.

```bash
# Go back to main
git checkout main

# Teammate changes the same line
echo 'print("Hello from the updated main branch!")' > app.py
git commit -am "Update greeting in main"
```

## Step 4: The Conflict!

Now, your feature is done, and you try to merge `main` into your feature branch to keep it up to date.

```bash
# Go back to your feature branch
git checkout feature/new-greeting

# Try to pull in main's changes
git merge main
```

**BOOM.** Git will yell at you: `Merge conflict in app.py. Automatic merge failed; fix conflicts and then commit the result.`

## Step 5: Resolving the Conflict

If you open `app.py` in your editor, you will see this:

```python
<<<<<<< HEAD
print("Hello from the AWESOME new feature!")
=======
print("Hello from the updated main branch!")
>>>>>>> main
```

- `<<<<<<< HEAD`: This marks the start of *your* changes (because your HEAD is currently on the feature branch).
- `=======`: The divider between your changes and the incoming changes.
- `>>>>>>> main`: The end of the incoming changes from `main`.

**To fix this:**
1. Delete all the git markers (`<<<<`, `====`, `>>>>`).
2. Keep the code you actually want. For example, maybe we want both!
   ```python
   print("Hello from the updated main branch!")
   print("And also, hello from the AWESOME new feature!")
   ```

## Step 6: Finalize the Merge

Once you have manually edited the file and saved it:

```bash
# Tell git you have resolved it
git add app.py

# Complete the merge commit
git commit -m "Merge main into feature/new-greeting, resolved conflict"
```

**Congratulations!** You just safely resolved a merge conflict, a daily reality for DevOps engineers.
