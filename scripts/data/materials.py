"""Curated starter GED and SAT study guides for `scripts/seed.py`."""

MATERIALS_DATA = [
    {
        "title": "GED Math: Linear Equations and Slope",
        "subject": "math",
        "topic": "algebra",
        "difficulty": "medium",
        "content": (
            "Linear equations form the backbone of the GED and SAT math sections. "
            "The standard slope-intercept form is y = mx + b, where m represents the slope (rise over run) "
            "and b represents the y-intercept (the point where the line crosses the vertical y-axis at (0, b)). "
            "To calculate the slope between two coordinates (x1, y1) and (x2, y2), use the formula m = (y2 - y1) / (x2 - x1). "
            "Parallel lines always possess identical slopes (m1 = m2). Perpendicular lines have negative reciprocal slopes "
            "(m1 * m2 = -1). When solving multi-step equations, always isolate the variable by applying inverse operations in reverse order of operations."
        ),
        "source": "Official GED Math Prep Guide",
    },
    {
        "title": "SAT Math: Quadratic Equations and Parabola Vertex",
        "subject": "math",
        "topic": "quadratics",
        "difficulty": "hard",
        "content": (
            "Quadratic equations appear in standard form: ax^2 + bx + c = 0. "
            "Solutions can be determined using the quadratic formula: x = (-b ± sqrt(b^2 - 4ac)) / (2a). "
            "The discriminant, b^2 - 4ac, determines the nature of the roots: "
            "if positive, there are two distinct real solutions; if zero, exactly one real repeated root; if negative, two complex conjugates. "
            "In vertex form, y = a(x - h)^2 + k, the coordinate (h, k) identifies the maximum or minimum turning point. "
            "The x-coordinate of the vertex can also be computed from standard form via h = -b / (2a)."
        ),
        "source": "Digital SAT Math Framework",
    },
    {
        "title": "SAT Reading: Main Idea & Rhetorical Synthesis",
        "subject": "reading",
        "topic": "main_idea",
        "difficulty": "hard",
        "content": (
            "SAT Reading questions test your ability to determine the central claim of paired passages and bulleted research notes. "
            "The main idea is the unifying argument that every paragraph supports, not merely a detail mentioned in a single paragraph. "
            "In rhetorical synthesis questions, read the student goal first before examining the notes. "
            "Watch out for extreme answer choices using words like 'always', 'never', 'impossible', or 'completely proven'. "
            "Correct answers paraphrase the thesis while maintaining the original author's tone and scope."
        ),
        "source": "College Board SAT Reading Framework",
    },
    {
        "title": "SAT Reading: Paired Passages and Cross-Text Connections",
        "subject": "reading",
        "topic": "cross_text",
        "difficulty": "hard",
        "content": (
            "Paired text questions require synthesizing two distinct perspectives on a single phenomenon or historical event. "
            "Text 1 typically presents an established scientific theory or foundational policy argument, "
            "while Text 2 introduces contradictory empirical data, technological qualifications, or an opposing philosophical school. "
            "When asked how the author of Text 2 would respond to a specific assertion in Text 1, "
            "locate the exact claim in Text 1, summarize Text 2's overarching stance, and select the choice that logically bridges the gap."
        ),
        "source": "Advanced SAT Verbal Strategy",
    },
    {
        "title": "GED Science: Cell Biology & Photosynthesis",
        "subject": "science",
        "topic": "biology",
        "difficulty": "medium",
        "content": (
            "Photosynthesis is the biological process by which autotrophic plants convert light energy, carbon dioxide, "
            "and water into glucose (sugar) and oxygen. The chemical equation is 6CO2 + 6H2O + light -> C6H12O6 + 6O2. "
            "Cellular respiration is the complementary metabolic pathway taking place inside mitochondria, converting glucose "
            "and oxygen into ATP energy, water, and carbon dioxide. On the GED Science test, experiments often measure the rate "
            "of oxygen production as an indicator of photosynthetic activity under varying light intensities."
        ),
        "source": "GED Science Core Competencies",
    },
    {
        "title": "GED Science: Mendelian Genetics & Punnett Squares",
        "subject": "science",
        "topic": "genetics",
        "difficulty": "medium",
        "content": (
            "Genetics on the GED focuses on predicting phenotypic and genotypic ratios of inheritance. "
            "Alleles are alternative forms of a gene, classified as dominant (capital letter) or recessive (lowercase letter). "
            "A homozygous individual carries identical alleles (BB or bb), whereas a heterozygous individual carries differing alleles (Bb). "
            "A monohybrid Punnett square crosses two heterozygous parents (Bb x Bb), yielding a 1:2:1 genotypic ratio (1 BB : 2 Bb : 1 bb) "
            "and a 3:1 phenotypic ratio (3 dominant trait : 1 recessive trait)."
        ),
        "source": "GED Life Sciences Review",
    },
    {
        "title": "SAT Writing: Subject-Verb Agreement & Punctuation",
        "subject": "writing",
        "topic": "grammar",
        "difficulty": "medium",
        "content": (
            "Subject-verb agreement requires that singular subjects take singular verbs and plural subjects take plural verbs. "
            "Intervening prepositional phrases (such as 'The box of old letters is heavy', not 'are heavy') often try to distract test-takers. "
            "For punctuation: semicolons (;) connect two independent clauses without a coordinating conjunction. "
            "Colons (:) must follow an independent clause and introduce an explanation, list, or dramatic elaboration. "
            "Dashes in pairs set off non-essential parenthetical information."
        ),
        "source": "SAT Writing & Language Guidelines",
    },
    {
        "title": "GED Social Studies: US Constitutional Principles & Separation of Powers",
        "subject": "social_studies",
        "topic": "civics",
        "difficulty": "medium",
        "content": (
            "The United States Constitution establishes a federal democratic republic organized around three structural pillars: "
            "separation of powers, checks and balances, and federalism. "
            "Article I vests legislative power in Congress; Article II vests executive power in the President; "
            "Article III vests judicial authority in the Supreme Court. "
            "Checks and balances prevent consolidation of power: the President may veto legislation, Congress can override a veto with a two-thirds vote, "
            "and the Supreme Court exercises judicial review to declare acts unconstitutional."
        ),
        "source": "GED Social Studies Civics Curriculum",
    },
]
