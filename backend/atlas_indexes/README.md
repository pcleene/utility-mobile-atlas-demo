# Atlas Search & Vector Search index definitions

Two indexes power the **Support** screen's hybrid search:

| File | Purpose | Cost |
|---|---|---|
| `support_text_idx.json` | BM25 lexical Atlas Search over `title`, `summary`, `embed_source.text` | Free on M10+ |
| `support_autoembed_idx.json` | Atlas Vector Search using **AutoEmbed → Voyage `voyage-4-large` (1024-d)** | Free on M10+ (Voyage tokens billed to your AI Provider Integration) |

The seed script (`python -m app.seed.seed_data`) issues both via
`createSearchIndexes`, but you can also apply them by hand:

## Atlas UI

1. Open your cluster → **Atlas Search** tab → **Create Search Index** → **JSON Editor**
2. Paste the contents of `support_text_idx.json` (omit the `_comment` and the
   top-level `name`/`collectionName` fields — the UI prompts for those).
3. Repeat for `support_autoembed_idx.json` under **Atlas Vector Search →
   Create Index → JSON Editor**.

## Atlas CLI

```bash
atlas search indexes create \
  --clusterName Cluster0 \
  --file backend/atlas_indexes/support_text_idx.json

atlas search indexes create \
  --clusterName Cluster0 \
  --type vectorSearch \
  --file backend/atlas_indexes/support_autoembed_idx.json
```

## Voyage AI prerequisite (AutoEmbed only)

The **AutoEmbed** field type tells Atlas to call your configured embedding
provider on every insert/update — application code never calls Voyage
directly. Configure it once per project:

1. Atlas → **Settings** (top-right) → **AI Provider Integrations**
2. Click **Add Integration → Voyage AI**
3. Paste your `VOYAGE_API_KEY` (from `.env`)
4. Save. The integration is now available to every cluster in the project.

Once the integration is live, AutoEmbed indexes report `status: READY,
queryable: true` once the initial corpus has been embedded — typically
under a minute for the seed's ~2,000 tickets.

Verify with:

```js
db.support_conversations.aggregate([{ $listSearchIndexes: {} }])
```
