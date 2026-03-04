"""
Seed script — populates the demo_items table with 15 pre-written sample saves.
Run once on deploy: python seeds/demo_data.py

Safe to re-run: existing rows are skipped on conflict.
"""

import sys
import os

# Allow running from the backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

# Alembic migrations use the sync URL — convert asyncpg → psycopg2 if needed
SYNC_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(SYNC_URL)
Session = sessionmaker(bind=engine)


DEMO_ITEMS = [
    # ── AI & Tech ────────────────────────────────────────────────────────────
    {
        "url": "https://openai.com/research/gpt-4",
        "title": "GPT-4 Technical Report",
        "summary": (
            "OpenAI's GPT-4 is a large multimodal model that accepts image and text inputs and produces text outputs. "
            "It exhibits human-level performance on various professional and academic benchmarks.\n\n"
            "• Achieves 90th percentile on the Uniform Bar Exam, compared to GPT-3.5's 10th percentile\n"
            "• Accepts image inputs, opening up new multimodal reasoning capabilities\n"
            "• Trained with RLHF to improve factuality and alignment with human intent\n"
            "• Scores above 95th percentile on AP exams across Biology, Calculus, and Psychology\n"
            "• Still has limitations: not fully reliable, makes reasoning errors, and has a fixed knowledge cutoff"
        ),
        "tags": ["GPT-4", "large language models", "multimodal AI", "OpenAI", "benchmarks"],
        "category": "AI & Tech",
        "source": "openai.com",
        "favicon_url": "https://openai.com/favicon.ico",
        "saved_date": datetime(2025, 1, 10, tzinfo=timezone.utc),
    },
    {
        "url": "https://www.wired.com/story/the-ai-revolution-in-search",
        "title": "The AI Revolution in Search Is Just Getting Started",
        "summary": (
            "A deep look at how AI-powered search engines are reshaping information discovery, moving from keyword matching to intent-based retrieval. "
            "Perplexity, Google's SGE, and Bing's Copilot are leading this shift.\n\n"
            "• Traditional PageRank is being augmented with embedding-based semantic search\n"
            "• Answer-first interfaces are replacing the classic list-of-links paradigm\n"
            "• Publishers worry about citation collapse as AI summaries reduce click-through rates\n"
            "• Retrieval-augmented generation (RAG) is the architecture powering most AI search products\n"
            "• The next frontier is personalised search that reasons over a user's saved knowledge"
        ),
        "tags": ["AI search", "Perplexity", "RAG", "information retrieval", "LLMs"],
        "category": "AI & Tech",
        "source": "wired.com",
        "favicon_url": "https://www.wired.com/favicon.ico",
        "saved_date": datetime(2025, 1, 22, tzinfo=timezone.utc),
    },

    # ── Product & Design ─────────────────────────────────────────────────────
    {
        "url": "https://www.paulgraham.com/good.html",
        "title": "How to Make Wealth",
        "summary": (
            "Paul Graham argues that wealth creation comes from building something people want — "
            "and that startups are an extreme sport version of this process, compressing decades of work into a few years.\n\n"
            "• Wealth ≠ money: money is just a medium of exchange for the wealth you create\n"
            "• Smallness enables measurement: in a small company you can directly see the effect of your work\n"
            "• Technology is a leverage multiplier — a small team can create value disproportionate to its size\n"
            "• The best way to get rich is to find a lever — something that can multiply your effort\n"
            "• Risk and reward are correlated: the high-growth startup path is genuinely harder than a salary job"
        ),
        "tags": ["startups", "wealth", "Paul Graham", "leverage", "entrepreneurship"],
        "category": "Product & Design",
        "source": "paulgraham.com",
        "favicon_url": "https://paulgraham.com/favicon.ico",
        "saved_date": datetime(2025, 2, 3, tzinfo=timezone.utc),
    },
    {
        "url": "https://www.nngroup.com/articles/ten-usability-heuristics/",
        "title": "10 Usability Heuristics for User Interface Design",
        "summary": (
            "Nielsen Norman Group's classic framework for evaluating UI usability. "
            "These 10 heuristics are the most widely used principles in UX design, equally applicable to web, mobile, and desktop products.\n\n"
            "• Visibility of system status: always keep users informed about what is happening\n"
            "• Match between system and the real world: speak the user's language, not system language\n"
            "• User control and freedom: support undo and redo to let users recover from mistakes\n"
            "• Error prevention is always better than good error messages\n"
            "• Recognition over recall: minimise cognitive load by making actions visible"
        ),
        "tags": ["UX", "usability", "heuristics", "Nielsen Norman", "design principles"],
        "category": "Product & Design",
        "source": "nngroup.com",
        "favicon_url": "https://www.nngroup.com/favicon.ico",
        "saved_date": datetime(2025, 2, 14, tzinfo=timezone.utc),
    },

    # ── Business & Finance ───────────────────────────────────────────────────
    {
        "url": "https://hbr.org/2007/07/the-flywheel-effect",
        "title": "The Flywheel Effect — Jim Collins",
        "summary": (
            "Jim Collins explains that there is no single defining moment in a great company's success. "
            "Breakthroughs come from turning a heavy flywheel — consistent effort that builds momentum over time.\n\n"
            "• The flywheel metaphor: no single push, but accumulated momentum from repeated consistent actions\n"
            "• Amazon's flywheel: more customers → more sellers → better selection → lower prices → more customers\n"
            "• Great companies never point to a single moment — success is always an evolutionary process\n"
            "• The doom loop: companies that lurch from strategy to strategy never build momentum\n"
            "• Leaders who understand the flywheel communicate it simply; it feels obvious in retrospect"
        ),
        "tags": ["strategy", "flywheels", "Jim Collins", "compounding", "business growth"],
        "category": "Business & Finance",
        "source": "hbr.org",
        "favicon_url": "https://hbr.org/favicon.ico",
        "saved_date": datetime(2025, 1, 30, tzinfo=timezone.utc),
    },
    {
        "url": "https://www.sequoiacap.com/article/growing-up-fast/",
        "title": "Growing Up Fast — Sequoia Capital",
        "summary": (
            "Sequoia's playbook for how early-stage founders should think about growth — specifically why premature scaling kills more startups than slow growth does.\n\n"
            "• Product-market fit is the only thing that matters before scaling\n"
            "• Hiring before product-market fit burns runway and creates organisational debt\n"
            "• Revenue is a lagging indicator; retention and engagement are the leading signals to watch\n"
            "• The best founders hire slowly and fire quickly — maintaining quality at every stage\n"
            "• 'Do things that don't scale' is not a euphemism for staying small — it's about learning fast"
        ),
        "tags": ["startups", "growth", "Sequoia", "product-market fit", "scaling"],
        "category": "Business & Finance",
        "source": "sequoiacap.com",
        "favicon_url": "https://www.sequoiacap.com/favicon.ico",
        "saved_date": datetime(2025, 2, 20, tzinfo=timezone.utc),
    },

    # ── World Affairs ────────────────────────────────────────────────────────
    {
        "url": "https://www.economist.com/leaders/2024/01/25/the-world-in-2024",
        "title": "The World in 2024: A Year of Elections",
        "summary": (
            "2024 is the biggest election year in history, with more than 4 billion people eligible to vote across 50+ countries. "
            "The Economist examines what is at stake globally.\n\n"
            "• The US, EU, India, and Indonesia all hold elections — each a pivotal contest\n"
            "• AI-generated disinformation is expected to influence at least a dozen national votes\n"
            "• Taiwan's election is the most geopolitically consequential, given rising China tensions\n"
            "• Democratic backsliding: incumbents in Hungary, Turkey, and Russia are tightening control\n"
            "• The 'polycrisis' of inflation, climate, and conflict is reshaping voter priorities worldwide"
        ),
        "tags": ["elections", "geopolitics", "democracy", "2024", "global affairs"],
        "category": "World Affairs",
        "source": "economist.com",
        "favicon_url": "https://www.economist.com/favicon.ico",
        "saved_date": datetime(2025, 1, 27, tzinfo=timezone.utc),
    },
    {
        "url": "https://foreignpolicy.com/2024/02/10/ai-arms-race-great-powers/",
        "title": "The AI Arms Race Between the Great Powers",
        "summary": (
            "The US, China, and EU are locked in a three-way race to lead AI — combining export controls, talent wars, and massive state investment. "
            "Foreign Policy maps the competitive landscape.\n\n"
            "• The US CHIPS Act and export controls on advanced chips are the central weapons of the AI war\n"
            "• China is investing $15 billion per year in domestic AI research and chip manufacturing\n"
            "• The EU's AI Act takes a regulatory approach that may disadvantage European innovation\n"
            "• Frontier AI capabilities are increasingly classified as strategic national assets\n"
            "• Talent is the real bottleneck — the global pool of researchers who can train frontier models is tiny"
        ),
        "tags": ["AI", "geopolitics", "US-China", "semiconductors", "great power competition"],
        "category": "World Affairs",
        "source": "foreignpolicy.com",
        "favicon_url": "https://foreignpolicy.com/favicon.ico",
        "saved_date": datetime(2025, 2, 12, tzinfo=timezone.utc),
    },

    # ── Science & Health ─────────────────────────────────────────────────────
    {
        "url": "https://www.nature.com/articles/d41586-024-00001-2",
        "title": "The Science of Longevity: What Actually Works",
        "summary": (
            "Nature reviews the evidence behind popular longevity interventions — separating what the data supports from what is marketing hype.\n\n"
            "• Caloric restriction extends lifespan in mice but evidence in humans remains inconclusive\n"
            "• Exercise is the single most robustly supported longevity intervention — even 150 min/week matters\n"
            "• Rapamycin (an mTOR inhibitor) extends lifespan in mice; human trials are underway\n"
            "• Sleep quality is a stronger predictor of healthspan than most supplements combined\n"
            "• Social connection is a consistent predictor of longevity — isolation is as harmful as smoking 15 cigarettes/day"
        ),
        "tags": ["longevity", "healthspan", "exercise", "sleep", "rapamycin"],
        "category": "Science & Health",
        "source": "nature.com",
        "favicon_url": "https://www.nature.com/favicon.ico",
        "saved_date": datetime(2025, 2, 1, tzinfo=timezone.utc),
    },
    {
        "url": "https://www.hubermanlab.com/episode/the-science-of-neuroplasticity",
        "title": "The Science of Neuroplasticity and Learning",
        "summary": (
            "Andrew Huberman explains how the brain physically rewires itself in response to experience — and what conditions maximise learning rate in adults.\n\n"
            "• Neuroplasticity is driven by the pairing of focused attention with a novel stimulus\n"
            "• Epinephrine (adrenaline) release after learning consolidates memories — stress in the right dose helps\n"
            "• Non-sleep deep rest (NSDR) and naps accelerate memory consolidation after a learning session\n"
            "• The first 25 years of life are a critical period; adult plasticity requires more deliberate effort\n"
            "• Cold exposure, exercise, and dopamine spikes are reliable ways to prime the brain for new learning"
        ),
        "tags": ["neuroplasticity", "learning", "Huberman", "memory", "neuroscience"],
        "category": "Science & Health",
        "source": "hubermanlab.com",
        "favicon_url": "https://www.hubermanlab.com/favicon.ico",
        "saved_date": datetime(2025, 2, 17, tzinfo=timezone.utc),
    },

    # ── Personal ─────────────────────────────────────────────────────────────
    {
        "url": "https://fs.blog/the-stoic-reading-list/",
        "title": "The Stoic Reading List — Farnam Street",
        "summary": (
            "A curated introduction to Stoic philosophy for modern readers — covering the core ideas, the key figures, and how to apply them to daily life.\n\n"
            "• Stoicism is not about suppressing emotion — it's about not being ruled by emotion\n"
            "• The dichotomy of control: focus only on what is within your power; accept everything else\n"
            "• Memento mori (remember you will die) is a tool for appreciation, not morbidity\n"
            "• Marcus Aurelius' Meditations is the most practical entry point for modern readers\n"
            "• Negative visualisation — imagining loss before it happens — builds resilience and gratitude"
        ),
        "tags": ["stoicism", "philosophy", "Marcus Aurelius", "resilience", "mental models"],
        "category": "Personal",
        "source": "fs.blog",
        "favicon_url": "https://fs.blog/favicon.ico",
        "saved_date": datetime(2025, 1, 5, tzinfo=timezone.utc),
    },
    {
        "url": "https://jamesclear.com/marginal-gains",
        "title": "Marginal Gains: How Tiny Improvements Lead to Remarkable Results",
        "summary": (
            "James Clear explores the concept of marginal gains — the idea that improving every small process by 1% leads to compounding improvements that add up to transformative change.\n\n"
            "• The British Cycling team improved by 1% in everything from seat ergonomics to sleep quality — and won 60% of Olympic gold medals\n"
            "• 1% better every day for a year means 37× better by year's end; 1% worse every day means near zero\n"
            "• Habits are the compound interest of self-improvement — small gains are invisible short-term\n"
            "• The key is choosing systems over goals: goals set a destination, systems drive daily progress\n"
            "• What looks like sudden breakthrough is almost always the result of long-accumulated marginal gains"
        ),
        "tags": ["habits", "marginal gains", "James Clear", "compounding", "systems"],
        "category": "Personal",
        "source": "jamesclear.com",
        "favicon_url": "https://jamesclear.com/favicon.ico",
        "saved_date": datetime(2025, 2, 8, tzinfo=timezone.utc),
    },

    # ── Reference ────────────────────────────────────────────────────────────
    {
        "url": "https://docs.python.org/3/howto/regex.html",
        "title": "Regular Expression HOWTO — Python Docs",
        "summary": (
            "Python's official guide to writing and using regular expressions with the re module. "
            "Covers syntax, patterns, groups, flags, and practical examples.\n\n"
            "• Use raw strings (r'...') to avoid double-escaping backslashes in patterns\n"
            "• re.compile() caches the pattern for reuse — always use it in loops\n"
            "• Named groups (?P<name>...) make complex patterns much more readable\n"
            "• The re.VERBOSE flag lets you add whitespace and comments inside patterns\n"
            "• Lookahead and lookbehind assertions ((?=...) and (?<=...)) match without consuming characters"
        ),
        "tags": ["Python", "regex", "programming", "reference", "re module"],
        "category": "Reference",
        "source": "docs.python.org",
        "favicon_url": "https://www.python.org/static/favicon.ico",
        "saved_date": datetime(2025, 1, 18, tzinfo=timezone.utc),
    },

    # ── YouTube ──────────────────────────────────────────────────────────────
    {
        "url": "https://www.youtube.com/watch?v=aircAruvnKk",
        "title": "But what is a neural network? — 3Blue1Brown",
        "summary": (
            "Grant Sanderson's iconic visual introduction to neural networks — one of the clearest explanations of deep learning ever made. "
            "Starts from first principles, no maths background required.\n\n"
            "• A neural network is layers of neurons where each neuron holds a number between 0 and 1\n"
            "• Weights and biases determine how activations in one layer influence the next\n"
            "• The last layer's activations represent the network's output — e.g., which digit it 'thinks' it sees\n"
            "• Training is the process of adjusting weights to minimise prediction error across millions of examples\n"
            "• The visual analogy of 'what makes neurons light up' builds strong intuition for feature learning"
        ),
        "tags": ["neural networks", "deep learning", "3Blue1Brown", "visualisation", "explainer"],
        "category": "AI & Tech",
        "source": "youtube.com",
        "favicon_url": "https://www.youtube.com/favicon.ico",
        "saved_date": datetime(2025, 1, 15, tzinfo=timezone.utc),
    },
    {
        "url": "https://www.youtube.com/watch?v=733m6qBH-jI",
        "title": "How I Built a $1M Business With No Money — My First Million",
        "summary": (
            "Sam Parr and Shaan Puri break down the playbook for bootstrapping a business from zero to seven figures without outside investment. "
            "Real case studies, not theory.\n\n"
            "• The fastest path to $1M is solving a painful problem for a small, well-defined audience willing to pay\n"
            "• Starting with services (consulting, freelancing) generates immediate cash flow to fund product development\n"
            "• Distribution matters more than product: 'sell first, build second' is a valid strategy\n"
            "• The best bootstrap stories share a pattern: extremely boring market, slightly better solution\n"
            "• Compounding customer relationships and referrals are the unfair advantage of bootstrapped companies"
        ),
        "tags": ["bootstrapping", "entrepreneurship", "business", "My First Million", "startups"],
        "category": "Business & Finance",
        "source": "youtube.com",
        "favicon_url": "https://www.youtube.com/favicon.ico",
        "saved_date": datetime(2025, 2, 25, tzinfo=timezone.utc),
    },
]


def seed():
    with Session() as session:
        inserted = 0
        skipped = 0
        for item in DEMO_ITEMS:
            exists = session.execute(
                text("SELECT 1 FROM demo_items WHERE url = :url"),
                {"url": item["url"]}
            ).fetchone()

            if exists:
                skipped += 1
                continue

            session.execute(
                text("""
                    INSERT INTO demo_items (url, title, summary, tags, category, source, favicon_url, saved_date)
                    VALUES (:url, :title, :summary, :tags, :category, :source, :favicon_url, :saved_date)
                """),
                {
                    "url": item["url"],
                    "title": item["title"],
                    "summary": item["summary"],
                    "tags": item["tags"],
                    "category": item["category"],
                    "source": item["source"],
                    "favicon_url": item["favicon_url"],
                    "saved_date": item["saved_date"],
                }
            )
            inserted += 1

        session.commit()
        print(f"Demo data seeded: {inserted} inserted, {skipped} already existed.")


if __name__ == "__main__":
    seed()
