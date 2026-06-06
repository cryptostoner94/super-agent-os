"""Stripe — defaults to test mode."""
import os, stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
LIVE = os.getenv("STRIPE_LIVE", "false").lower() == "true"

async def create_invoice(payload: str):
    import json
    d = json.loads(payload) if isinstance(payload, str) else payload
    cust = stripe.Customer.create(email=d["email"], name=d.get("name",""))
    stripe.InvoiceItem.create(customer=cust.id, amount=int(d["amount_usd"]*100), currency="usd",
                              description=d.get("description","Service"))
    inv = stripe.Invoice.create(customer=cust.id, collection_method="send_invoice", days_until_due=7)
    inv.send_invoice()
    return {"invoice_id": inv.id, "hosted_url": inv.hosted_invoice_url, "live": LIVE, "amount_usd": d["amount_usd"]}

async def list_payments(_=""):
    return {"payments":[p.to_dict_recursive() for p in stripe.PaymentIntent.list(limit=10).data]}

async def charge(payload: str):
    import json
    d = json.loads(payload)
    if d.get("amount_usd",0) > float(os.getenv("WARDEN_APPROVAL_THRESHOLD","100")):
        return {"error":"requires_human_approval"}
    pi = stripe.PaymentIntent.create(amount=int(d["amount_usd"]*100), currency="usd",
                                     customer=d["customer_id"], confirm=True)
    return {"id": pi.id, "status": pi.status, "amount_usd": d["amount_usd"]}
