# Demo E-Commerce Repository for CodePilot AI

This repository contains a full-stack demo application with frontend (TypeScript), backend (Python FastAPI), services, controllers, authentication, order processing, and payment integrations.

It includes realistic architecture, code patterns, and intentional bug scenarios for testing AI repository analysis:
1. **Duplicate Order Bug**: `backend/routes/order_routes.py` line 45 (Race condition in idempotency check).
2. **Missing Authorization Check**: `backend/routes/auth_routes.py` line 78 (Missing ownership check before updating user profile).
3. **Unhandled Promise Rejection**: `src/services/paymentService.ts` line 32 (Missing try/catch block during payment retry).
