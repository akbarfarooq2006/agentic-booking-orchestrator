# AI Service Orchestrator for Informal Economy

Status: Not started. This README captures the agreed project scope and planned structure.

## Overview
Build an agentic AI system that automates the end-to-end lifecycle of a service request (intent to booking and follow-up) for informal economy services such as plumbers, electricians, tutors, beauticians, and home service providers.

This project must use Google Antigravity as the core orchestration platform for multi-step reasoning, tool use (Maps, Search, APIs), and action execution.

## Problem Statement
Users currently rely on WhatsApp messages, phone calls, and referrals, causing inefficient matching and poor user experience. The system should understand natural language requests, find providers, recommend the best option, simulate booking, and handle follow-up automation with traceable reasoning and logs.

## Key Requirements
- Understand user requests in Urdu, Roman Urdu, and English.
- Extract service type, location, and time from natural language.
- Discover providers using mock data or Google Maps/Places.
- Rank providers by distance, availability, and rating.
- Select or recommend providers with clear reasoning.
- Simulate booking, confirmation, scheduling, and reminders.
- Demonstrate agentic workflow with planning, decision, action, and follow-up.
- Provide traceable logs of decisions, tool usage, and actions.

## Example User Scenario
Input:
"Mujhe kal subah G-13 mein AC technician chahiye"

Expected Output (example):
- Service Request: AC Technician
- Location: G-13
- Time: Tomorrow morning
- Recommended Provider: Ali AC Services (2.1 km away)
- Reasoning: Closest available provider with high rating
- Simulated Booking: Slot booked at 10:00 AM, confirmation sent
- Follow-up: Reminder scheduled 1 hour before appointment

## Planned Architecture (Draft)
- Client: Mobile app (required), web app (optional)
- Orchestration: Google Antigravity
- Agents/Steps:
  - Intent parser
  - Provider discovery
  - Ranking and recommendation
  - Booking simulation
  - Follow-up automation
  - Trace logging
- Data:
  - Mock provider dataset (initial)
  - Optional Google Maps/Places API integration

## Deliverables
- Working prototype (mobile app required)
- Optional web app
- Demo video (3 to 5 minutes)
- Agent trace/logs showing reasoning and actions
- Documentation describing architecture and Antigravity usage

## Evaluation Criteria (Target)
- Antigravity usage and orchestration (25%)
- Agentic reasoning and workflow (20%)
- Matching quality and decision logic (20%)
- Action simulation and execution (15%)
- Technical implementation (10%)
- Innovation and UX (10%)

## Assumptions and Constraints
- Use mock data if real APIs are unavailable.
- Avoid real personal or sensitive data.
- At least one booking must be simulated end-to-end.

## Setup (Placeholder)
To be defined once the project is initialized.

## Run (Placeholder)
To be defined once the project is initialized.

## Tech Stack (Placeholder)
To be finalized. Likely includes:
- Google Antigravity for orchestration
- Mobile framework (TBD)
- Optional web frontend (TBD)
- Storage for mock bookings/logs (TBD)

## Next Steps
- Finalize tech stack and repo structure
- Define mock provider dataset schema
- Outline Antigravity workflow and tools
- Build minimal mobile UI for input/output
- Implement booking simulation and logs
