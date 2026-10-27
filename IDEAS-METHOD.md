# The battle of ideas: method note

Study of the French vs Japanese war on X, 17 to 26 October 2026. STATUR viral marketing lab.
Live map: https://lkorczowski.github.io/france-vs-japan-X-trend/ideas.html
Analysis run on 2026-10-27. Annotator: Claude (Opus 5.5), to be reviewed by Dr. Louis Korczowski.

## 1. Question

You cannot understand an attention war without mapping the ideas in conflict. We ask three questions:
1. Which ideas carried the virality?
2. Which idea wins when one answers another?
3. Which camp owns each idea: French, Japanese, or a third party?

## 2. Corpus

| Source | Posts | How |
|---|---|---|
| Seed posts | 59 | Every tracked post above 500K views, plus posts collected by hand on X search |
| Posts quoted by seeds | 8 | X API expansion of referenced posts |
| Origin posts | 2 | Seen in screenshots shared by Japanese accounts (no ID) |
| Quotes | 115 | Read in the Quotes tab of the 15 most viewed posts, in Chrome, sorted by views |
| **Total** | **182 posts, about 243M views** | |

API cost of the study: one lookup of 69 posts, about 0.35 USD. The quotes were read in the browser, at no API cost.

## 3. Reading protocol

Each post was read with its picture. A contact sheet of every photo and video thumbnail was built and inspected, because the joke often lives in the image (MemeCap shows that vision-language models still struggle with visual metaphors, which is why this step is explicit).

Each post received one annotation:

| Field | Values |
|---|---|
| idea | The claim in one neutral English sentence, including the implied meaning of the joke |
| concept | The contested ground, independent of camp (21 concepts) |
| side | The camp the idea serves: FR, JA or NEU |
| community | Who posts: FR, JA, EN, AR, ES, TH, PT, CN (language and self-identification) |
| register | humor, insult, argument, info, testimony, meta |
| rel | For quotes: rebut, amplify, verdict or restate |

The camp is a reading of the post, never an assumption about the origin or religion of its author.

## 4. Concept induction

The concepts were induced from the posts, not fixed in advance, following concept induction (LLooM, Lam et al. 2024). The first hypothesis list had 16 ideas. Reading the corpus produced 21 concepts, among which several we had not anticipated: the spectators' verdict, auto-translation as a weapon, old grudges joining in (Korea, China, Brazil, the Arab world), and the correction by data.

| ID | Concept | Views | Posts | Serves | Elo | W-L |
|---|---|---|---|---|---|---|
| K03 | Japan's sexual taboos | 32.2M | 10 | FR 84%, JA 16% | 1469 | 0-2 |
| K02 | Absurd appropriation | 29.1M | 14 | FR 84%, JA 16% | 1517 | 1-0 |
| K07 | A Muslim and immigrant riot | 23.7M | 17 | JA 94%, FR 6% | 1527 | 8-6 |
| K14 | The spectators' verdict | 22.0M | 29 | FR 88%, NEU 8%, JA 4% | 1483 | 0-1 |
| K04 | Suicide jokes | 21.7M | 4 | FR 100% | 1530 | 2-0 |
| K01 | Who owns anime | 13.5M | 10 | JA 44%, FR 39%, NEU 17% | 1547 | 4-1 |
| K21 | Why are they fighting? | 12.7M | 11 | NEU 60%, FR 40% | 1500 | 0-0 |
| K05 | Overwork and submission | 12.3M | 6 | FR 100% | 1460 | 1-4 |
| K16 | Love for Japan, lost or kept | 10.2M | 6 | FR 76%, NEU 12%, JA 12% | 1499 | 1-1 |
| K06 | The bomb and WWII | 10.2M | 7 | FR 72%, JA 28% | 1482 | 2-3 |
| K12 | France in decline | 7.7M | 6 | JA 100% | 1500 | 0-0 |
| K13 | The riot's real victims | 7.5M | 4 | JA 100% | 1500 | 0-0 |
| K15 | Auto-translation | 7.4M | 9 | FR 99% | 1454 | 0-3 |
| K19 | Who started it | 7.3M | 8 | JA 74%, NEU 14%, FR 12% | 1542 | 4-1 |
| K10 | Who is really French | 5.9M | 10 | JA 95%, FR 5% | 1475 | 2-4 |
| K11 | Japanese racism | 5.5M | 8 | FR 64%, JA 36% | 1455 | 1-4 |
| K08 | Students born in France | 4.3M | 4 | NEU 76%, JA 24% | 1590 | 6-0 |
| K17 | Old grudges join in | 4.0M | 5 | JA 60%, FR 30%, NEU 11% | 1470 | 0-2 |
| K09 | What the media hides | 3.1M | 6 | JA 100% | 1500 | 0-0 |
| K20 | French insolence | 2.0M | 7 | FR 100% | 1500 | 0-0 |
| K18 | Foreign money behind the riots | 1.3M | 1 | JA 100% | 1500 | 0-0 |

## 5. Metrics

- **Reach of an idea**: sum of the views of the posts that carry it.
- **Ratio of a duel**: when post B quotes post A with another idea, ratio = views of B / views of A. Above 1, the answer won.
- **Elo of a concept**: every rebuttal is a match between the concept of the answer and the concept of the original, in chronological order, K = 32, start at 1500. The answer wins the match when its ratio is above 1. Rebuttals inside the same concept count as duels between camps, not as Elo matches.
- **Third-party share**: views of posts from communities other than French and Japanese speakers.

## 6. Map

- Each idea sentence is embedded with all-mpnet-base-v2.
- Concept centroids are compared by cosine distance and placed in 2D by metric MDS, as in the intertopic distance map of LDAvis (Sievert and Shirley 2014). This was also the visual language of our earlier Tinnitus-NLP work with LDA and pyLDAvis.
- The "battle lines" view places each concept on the horizontal axis by the share of its views serving each camp, and keeps the MDS vertical axis.
- UMAP and t-SNE of single ideas are computed for comparison (analysis/projections.json).

## 7. Can it be automated? First test

We clustered the posts automatically into 21 groups (Ward linkage) and compared them with the hand-induced concepts, using the adjusted Rand index (1 = perfect agreement, 0 = chance).

| Input | Model | ARI |
|---|---|---|
| Raw post text, multilingual | paraphrase-multilingual-mpnet-base-v2 | 0.11 |
| Annotated idea sentences | paraphrase-multilingual-mpnet-base-v2 | 0.15 |
| Annotated idea sentences | all-MiniLM-L6-v2 | 0.15 |
| Annotated idea sentences | all-mpnet-base-v2 | 0.21 |

Reading: sentence embeddings of raw posts recover almost nothing of the concepts. Writing out the implied meaning of each post helps, and the rest of the gap is reasoning: knowing that "his feet do not touch the ground" is a suicide joke, or that Vegeta eating a pig is an argument about Islam. That step needs a model that sees the image and resolves the joke. The automation path we propose:

1. Collect: seeds by reach, then quotes ranked by views (browser or API).
2. Read: a vision-language model writes, for each post, a literal caption and the implied idea (MemeCap-style).
3. Induce: concept induction on the implied ideas (LLooM or TopicGPT), with a human validating the concept list.
4. Assign and measure: concept, camp and relation per post, then ratios, Elo and the map.
5. Audit: a human relabels a random 10% and every low-confidence post. Agreement is reported.

## 8. Findings

1. **French jokes won the attention war.** Ideas serving the French side earned 147M views, against 79M for the Japanese side and 18M neutral. The four biggest French themes are jokes: sex, appropriation, suicide and work.
2. **Humor beat argument, except on one front.** The biggest Japanese idea is a frame, not a joke: the riots are a Muslim and immigrant revolt (23.7M). It drew Arabic-speaking accounts into the fight, who answered with the "submission to America" idea.
3. **One view in five came from neither camp (21%).** English-speaking spectators acted as the jury (22M views of verdicts). One of the most viewed "French" jokes, 7.6M views, was posted by an English speaker who says he was "larping French".
4. **The correction won every duel it fought.** A Japanese post showing that most of those arrested were French nationals born in France (2.7M) was never out-reached by its rebuttals: 6 wins, 0 losses, the best Elo of the map.
5. **Auto-translation was the weapon.** X translated every insult in both directions. Spectators turned it into the punchline ("Translated from French").
6. **One answer beat its original.** "Stop soiling Japanese culture" (2.35M) was out-reached by a French insult answering it (2.48M), ratio 1.06.

## 9. Origin of the conflict

- 17 Oct: high-school protests in France turn into riots and looting.
- 18 Oct: a French post shows a Naruto (Obito) cosplayer at a burning car, about 2.3M views.
- 18 Oct: a Japanese account asks the French to stop soiling Japanese culture, 2.35M views.
- 18 Oct: French answers ask Japan to withdraw every anime inspired by Europe (5.1M) and list Japanese "vices" (about 2.3M), the script of the jokes that follow.
- 19 to 22 Oct: Japanese X frames the riots as Muslim and immigrant. A minority answers with arrest data.
- 21 to 25 Oct: the French joke wave (Vegeta is Algerian, 17.9M), amplified by English-speaking spectators.

## 10. Limits

- Seed posts were partly chosen by hand: the corpus favours the most viral posts, and the French side is over-represented among them.
- Views measure reach, not agreement. An idea can travel because it shocks.
- One annotator. Concepts and camps must be checked by a second reader before publication.
- Quotes were read in a logged-in browser: the order and the counts of the Quotes tab can change over time.
- The API cannot see protected or deleted posts.

## 11. Ethics and display rules

- No post text is displayed. Ideas are paraphrased in neutral language.
- Posts labelled as insults, and any post matching the slur blocklist, are counted but never linked.
- Sides are languages and positions, never ethnicity or religion.

## 12. Files

| File | Content | Public |
|---|---|---|
| docs/ideas.html | The map page | yes |
| docs/data/ideas.json | Concepts, ideas, duels, communities (no post text) | yes |
| ideas/annotations.py | The annotation of every post (paraphrased ideas, no post text) | yes |
| ideas/build_ideas.py | Embeddings, MDS, duels, Elo, ARI | yes |
| analysis/ | Raw corpus, quote captures, images | no (contains post text) |

## References

- Lam, M., Teoh, J., Landay, J., Heer, J., Bernstein, M. Concept Induction: Analyzing Unstructured Text with High-Level Concepts Using LLooM. CHI 2024. https://arxiv.org/abs/2404.12259
- Pham, C. M., Hoyle, A., Sun, S., Resnik, P., Iyyer, M. TopicGPT: A Prompt-based Topic Modeling Framework. NAACL 2024. https://arxiv.org/abs/2311.01449
- Grootendorst, M. BERTopic: Neural topic modeling with a class-based TF-IDF procedure. arXiv 2022. https://arxiv.org/abs/2203.05794
- Hwang, E., Shwartz, V. MemeCap: A Dataset for Captioning and Interpreting Memes. EMNLP 2023. https://aclanthology.org/2023.emnlp-main.89
- Sievert, C., Shirley, K. LDAvis: A method for visualizing and interpreting topics. Workshop on Interactive Language Learning, Visualization, and Interfaces, 2014.
