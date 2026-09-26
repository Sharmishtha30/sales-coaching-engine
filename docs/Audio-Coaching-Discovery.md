# Audio coaching micro-SaaS — discovery v0.1

Date: 26 September 2026
Status: Discovery; no architecture or implementation approved.

## Founder brief
Build a standalone service accepting audio files, separating speakers, asking a human to confirm their identities, retaining confirmed names and voice references for future calls, converting conversations to structured data, classifying call intent, and producing context-specific feedback. Initial use cases: sales calls and interview preparation. Retain history to improve future analysis and feedback. Evaluate API and MCP delivery before deciding.

## Process and deliverables
1. Discover buyer, user, recurring problem, existing alternatives and pilot access.
2. Research market, competitors and open source; compare build, buy and integrate options, pricing, licensing and differentiation. Distinguish vendor claims from tested capability.
3. Produce PRD: target customer, workflows, scope, data lifecycle, success metrics and acceptance criteria.
4. Produce TRD after product alignment: interfaces, schema, speaker matching, correction propagation, memory retrieval, evaluation, security, costs and deployment.
5. Build and validate only after the PRD and TRD are agreed. Deliver a usable business pilot, documentation and operating instructions.
6. Preserve research, decisions and revisions in documents and Git. Remote repository remains unspecified; nothing has been pushed.

## Initial market signals — preliminary, not exhaustive
- Gong advertises sales-call coaching and progress tracking: https://www.gong.io/sales-coaching-software
- Yoodli advertises interview preparation and progress tracking: https://yoodli.ai/use-cases/interview-preparation
- pyannoteAI documents enrolling voiceprints and identifying recurring speakers: https://www.pyannote.ai/blog/speaker-identification-system-recurring-meetings

Implication: transcription, speaker memory and longitudinal coaching are not sufficient evidence of a unique moat. Investigate a specific underserved workflow and measurable advantage. These are official vendor descriptions, not independent performance verification.

## Hypotheses to test
- A focused initial customer segment will yield clearer evaluation and distribution than launching sales and interview coaching equally.
- Human-corrected, timestamp-grounded feedback linked to subsequent behavior and outcomes may create value; differentiation remains unproven.
- API and MCP may be complementary delivery interfaces; choose based on actual consuming workflows.
- Persistent speaker identity and persistent coaching context are separate needs. A known user ID may sometimes replace voice matching.

## Discovery questions — round one
1. Who are the first five actual users and who pays? Which use case can supply recordings and feedback soonest?
2. Sales: actual prospect calls or practice? Interviews: self-practice, mock interviews, AI conversations or real interviews? Whose performance is evaluated?
3. What do users do today, what fails, and what concrete decision should our feedback change?
4. Give an example of valuable feedback and what would count as measurable improvement after five calls.
5. Which history should persist: voice identity, goals, weaknesses, past feedback, domain context, outcomes? Who may view it?
6. Must voices be recognized automatically when identity could be supplied? Who confirms a new speaker and may authorize retaining their voice reference? Can users delete it independently of transcripts?
7. Who consumes the product: developers, an LMS/CRM, coaches/managers, individuals or an assistant using MCP? Is a small review UI needed?
8. Initial languages, accent/code-switching needs, audio sources, call length/volume, acceptable processing time, budget and pilot date?
9. Which private Git repository should hold the documents and eventual code?

## Open research work
Full product/user/market analysis; direct and adjacent competitor matrix; open-source model and license review; demand validation; defensibility; unit economics; privacy requirements; evaluation design. No market-size, price, accuracy or product-market-fit claims established yet.
