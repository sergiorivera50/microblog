# microblog

This repo is my live implementation of a minimal static site generator that serves as my microblog where I post various 
forms of content.

I built this over a weekend having been inspired by frameworks like [Hugo](https://gohugo.io/) or 
[Jekyll](https://jekyllrb.com/) but realizing that they contain waaay to many features I'd ever need.

My passion is in applied mathematics and machine learning, and, though I appreciate frontend tools like these, I'd 
rather focus on what really matters to me, which is producing and distributing content that helps other people with
similar interests.

Hence, why I created this. A super-lightweight static-site generator covering:

- Markdown support for writing content (duh).
- Dynamic templates for individual posts, lists, and top-level sections.
- Asset management for handling markdown-embedded figures.
- Metadata handling via frontmatter.
- Tag support (with filtering).
- Math rendering using KaTeX (client-side).
- Integration with Obsidian as text editor.
- Automated deployment to GitHub pages.

And much more. All being extremely opinionated and optimized for my personal workflows.

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

## Future Plans

- Instead of imposing `content/blog` to be an Obsidian vault, I should add a "mode" in which you `build` the site from
a path (which can be the folder of an already existing Obsidian vault). This adds a bit of complexity because it would
require an additional step in which attachments are located and moved into its appropriate post folder. But, essentially,
the user experience would remain the same: you make changes on a file and see them directly applied through the live
server (if in development). Ideally copying files is not expensive and can be implemented with low friction. This path
could be specified through the `site.toml` file.
- `styles.css` needs to be updated to make all font sizes use `rem` rather than `px` for accesibility purposes.
- I might want to have an automated conversion of content images to `webp` format for optimization purposes.
