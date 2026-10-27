# Idea analysis code

Annotation and analysis of the French vs Japanese war on X. Method: ../IDEAS-METHOD.md.

- annotations.py: one annotation per post (paraphrased idea, concept, side, community, register, quote relation). No post text.
- build_ideas.py: embeddings, MDS map, duels, Elo, ARI. Writes docs/data/ideas.json.
- eval_clusters.py, eval_raw.py: the automation test (clustering vs hand concepts).

The scripts read a private corpus (analysis/, not published) that contains post text and media.
