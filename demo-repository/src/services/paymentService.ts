export interface PaymentRequest {
  orderId: string;
  amount: number;
  currency: string;
  paymentMethodToken: string;
}

export class PaymentService {
  async processPayment(request: PaymentRequest): Promise<{ transactionId: string; status: string }> {
    // Intentional issue: missing retry error handling logic
    const res = await fetch('/api/v1/payments/charge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    
    // Bug scenario: direct call to json() without checking res.ok can cause unhandled promise rejection
    const data = await res.json();
    return {
      transactionId: data.transaction_id,
      status: data.status
    };
  }
}
