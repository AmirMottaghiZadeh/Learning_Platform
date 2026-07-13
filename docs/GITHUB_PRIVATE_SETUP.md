# Private GitHub Setup

This project is ready to be pushed to a private GitHub repository from the project root:

```bash
cd "/home/amir/Documents/Learning Platform Architecture & Engineering Book"
git init
git add .
git status
git commit -m "Initial private repository import"
git branch -M main
git remote add origin git@github.com:<OWNER>/<PRIVATE_REPO>.git
git push -u origin main
```

Before the first commit, verify that these files are ignored:

```bash
git status --ignored --short
```

Expected ignored examples:

- `backend/.env`
- `backend/.venv/`
- `backend/backups/`
- `frontend/node_modules/`
- `frontend/.expo/`

If Git reports any of those as tracked/staged, stop and unstage them before committing.

## Recommended GitHub Settings

- Repository visibility: Private.
- Enable branch protection for `main` after the first push.
- Require status checks once GitHub Actions runs successfully.
- Do not add production secrets to the repo. Use GitHub Actions secrets or deployment provider environment variables.

## Local Verification Before Push

```bash
cd backend
rtk .venv/bin/python manage.py check
rtk .venv/bin/python manage.py test

cd ../frontend
rtk npm run typecheck
```
