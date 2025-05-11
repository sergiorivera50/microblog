# microblog

## Posting a new article

**Step 1: Start local server** (optional)

```bash
poetry run serve
```

**Step 2: Create a new post**

This action will automatically open up an [Obsidian](https://obsidian.md/) vault focused on the new post to start writing.

```bash
poetry run new
```

**Step 3: Pushing changes**

```bash
git add content/blog
git commit -m "blog update"
git push
```

**CI/CD Pipeline**

On the background, GitHub Actions will execute `poetry run build` to generate the static site and deploy it to [sergiorivera.dev](https://www.sergiorivera.dev/)