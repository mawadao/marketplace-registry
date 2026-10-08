# mawaDao marketplace registry

The open list of AI tools and agents shown on mawaDao. People, students and educators use it to
explore and learn about new and trending AI tools; developers use it to list their tools and to
offer their agents in the mawaDao marketplace.

mawaDao brings together agentic AI and blockchain technologies to create an open,
community-owned ecosystem for education. There are no listing fees, no creation fees and no
commissions. When a product earns money, 75% goes to the community who built it and 25% goes
to mawa to educate deserving children, orphans and street children.

## What's in it

| Folder | What |
| --- | --- |
| [`tools/`](tools) | AI tools, frameworks, MCP servers and services |
| [`agents/`](agents) | mawas, after community review |

Both are merged into one catalog on [mawadao.com/marketplace](https://mawadao.com/marketplace).
Every listing is one YAML file and follows [`schema/listing.schema.json`](schema/listing.schema.json).

## Pricing by type of user

Each listing shows its price and usage limits for three types of user:

| Type | Who |
| --- | --- |
| `education` | Students, teachers, schools, orphanages and non-profits |
| `individuals` | People using it for themselves |
| `business` | Companies and businesses |

**Agents must be free for education.** Listing is always free, and there is no commission on
educational use. How larger organisations pay for agents is still being decided with the
community, so for now list `business` as `price: contact` if you don't offer it free. When an
agent is monetised, mawaDao's 75/25 revenue split applies. Questions:
[mawadao.com/#contact](https://mawadao.com/#contact).

## List your tool or agent

1. Fork this repository.
2. Copy [`templates/tool.yaml`](templates/tool.yaml) to `tools/<name>.yaml`, or
   [`templates/agent.yaml`](templates/agent.yaml) to `agents/<name>.yaml`. The file name is the
   listing's address on mawaDao, so use lowercase letters, digits and hyphens.
3. Fill it in. Write the summary in your own words.
4. Check it locally (optional):

   ```bash
   pip install -r requirements.txt
   python scripts/validate.py
   ```

5. Open a pull request. CI checks the file; a maintainer reviews it. Agents also go through
   community safety review (age suitability, data collection, fairness) before they appear in
   the marketplace.

Once merged, the listing appears on mawaDao after the next index build.

## How the index is built

`scripts/build_index.py` combines every listing with live public facts from GitHub (stars,
forks, language, last activity) and writes `dist/index.json`. The publish workflow runs on every
merge and once a week, and serves the result from GitHub Pages:

```
https://mawadao.github.io/marketplace-registry/index.json
```

"Trending" is the number of stars a project gained since the previous weekly build.

## Licence

Apache 2.0. See [LICENSE](LICENSE).
