BENCHMARK_QUESTIONS = [
    {
        "id": "q1",
        "question": "Where is authentication implemented?",
        "expected_files": ["src/auth/AuthProvider.ts", "backend/routes/auth_routes.py"]
    },
    {
        "id": "q2",
        "question": "How does order creation work?",
        "expected_files": ["src/services/orderService.ts", "backend/routes/order_routes.py"]
    },
    {
        "id": "q3",
        "question": "Which module handles payment processing?",
        "expected_files": ["src/services/paymentService.ts", "backend/services/payment_gateway.py"]
    },
    {
        "id": "q4",
        "question": "Find potential security vulnerabilities in authentication.",
        "expected_files": ["backend/routes/auth_routes.py"]
    },
    {
        "id": "q5",
        "question": "Where is the duplicate order bug located?",
        "expected_files": ["backend/routes/order_routes.py"]
    }
]
