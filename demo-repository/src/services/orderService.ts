export interface OrderItem {
  productId: string;
  quantity: number;
  price: number;
}

export interface CreateOrderPayload {
  customerId: string;
  items: OrderItem[];
  shippingAddress: string;
  idempotencyKey?: string;
}

export class OrderService {
  private apiBase = '/api/v1/orders';

  async createOrder(payload: CreateOrderPayload) {
    const response = await fetch(`${this.apiBase}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': payload.idempotencyKey || `ik_${Date.now()}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.message || 'Order creation failed');
    }

    return await response.json();
  }

  async getOrderById(orderId: string) {
    const response = await fetch(`${this.apiBase}/${orderId}`);
    return await response.json();
  }
}
