# Build-in-public post: starting draft

The post must explain **one real decision and one real limitation**. This draft uses things that are true of this project. Rewrite it in your voice, and delete anything that isn't true for you.

---

I built a bakery, coffee and flower shop website, with a chatbot that's allowed to say "I'm not sure". (The shop is fictional. The project is real.)

**One decision:** every price, hour and rule lives in a single `shop.json`. The menu pages, the order form rules and the chatbot all read it, so the website and the bot can't disagree. I found that out the hard way: my first info sheet listed a gluten-free cookie that wasn't on the menu.

**One limitation:** when my API credits ran out I added an offline chatbot engine so the site never breaks. It's rule-based and English-only, so unusual phrasings get a polite "I'm not sure" rather than a clever answer. I tested it with 41 questions (36/38 on my first run, 41/41 now), but I wrote the tests and the engine together, so I'm treating that 100% with suspicion.

Built with Claude as a pair-programmer; I [what you checked yourself].

Live: [URL]  ·  Code: [repo URL]

---

Add: a screenshot of the neon hero, or a 10-second screen recording of the 3D bouquet.
