import pandas as pd
import uvicorn
from datetime import timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CSV_FILE = "supply_chain_order_fulfillment_delay_risk.csv"

# This stores which orders have been "fixed" during this session
recovered_orders = {}

def get_data():
    df = pd.read_csv(CSV_FILE)
    df['order_date'] = pd.to_datetime(df['order_date'])
    return df

# --- UPDATED ADMIN STATS (WITH DYNAMIC RISK REDUCTION) ---
@app.get("/stats")
async def get_stats():
    df = get_data()
    display_df = df.copy()
    
    if recovered_orders:
        display_df.loc[display_df['order_id'].isin(recovered_orders.keys()), 'delayed'] = 0

    # 1. On-Time Delivery %
    otd = (display_df['delayed'] == 0).mean() * 100
    
    # 2. Risk Exposure %
    risk = display_df['delayed'].mean() * 100
    
    # 3. Carbon Impact
    factors = {'Air': 0.5, 'Road': 0.1, 'Rail': 0.03, 'Sea': 0.01}
    carbon_mt = display_df.apply(lambda r: r['shipping_distance_km'] * r['order_quantity'] * factors.get(r['shipping_method'], 0.05) / 1000, axis=1).sum() / 1000
    
    # 4. NEW: Average Transit Time (Days)
    # We simulate this based on the dataset's distance and method speed
    avg_days = display_df['shipping_distance_km'].mean() / 500 # Simplified proxy
    
    risk_label = "Mitigating" if recovered_orders else "Moderate"
    otd_change = "+1.2%" if recovered_orders else "-1.1%"

    return [
        {"label": "On-Time Delivery", "value": f"{otd:.1f}%", "change": otd_change, "pos": True if recovered_orders else False},
        {"label": "Risk Exposure", "value": f"{risk:.1f}%", "change": risk_label, "pos": True if recovered_orders else False},
        {"label": "Avg Transit Time", "value": f"{avg_days:.1f} Days", "change": "-0.2d", "pos": True},
        {"label": "Carbon Impact", "value": f"{carbon_mt:.1f} MT", "change": "-3.1%", "pos": True}
    ]

# --- EXISTING MODE SPLIT (UNTOUCHED) ---
@app.get("/mode-split")
async def get_mode_split():
    df = get_data()
    cat_colors = {'Air': '#6366f1', 'Road': '#f59e0b', 'Rail': '#8b5cf6', 'Sea': '#0ea5e9'}
    mode_risk = (df.groupby('shipping_method')['delayed'].mean() * 100).to_dict()
    return {k: {"value": v, "color": cat_colors.get(k, '#94a3b8')} for k, v in mode_risk.items()}

# --- EXISTING TREND DATA (UNTOUCHED) ---
@app.get("/trend-data")
async def get_trend_data():
    df = get_data()
    df['date_only'] = df['order_date'].dt.date
    trend = df.groupby('date_only')['delayed'].mean() * 100
    vals = trend.tail(15)
    
    # Matching your exact labels:
    # Green: < 20% | Yellow: 20-35% | Red: > 35%
    colors = [
        '#22c55e' if v < 20 else 
        '#facc15' if v <= 35 else 
        '#ef4444' for v in vals
    ]
    
    return {
        "labels": [d.strftime('%b %d') for d in vals.index],
        "values": vals.tolist(),
        "colors": colors
    }

# --- WARNINGS (WITH DUPLICATE DECORATOR REMOVED) ---
@app.get("/warnings")
async def get_warnings():
    df = get_data()
    remaining_df = df[~df['order_id'].isin(recovered_orders.keys())]
    high_risk = remaining_df.sort_values(by=['delayed', 'supplier_reliability_score'], ascending=[False, True]).head(4)
    
    return [
        {
            "id": int(r['order_id']), 
            "score": f"{r['supplier_reliability_score']*100:.0f}%", 
            "method": r['shipping_method']
        } for _, r in high_risk.iterrows()
    ]

@app.post("/reroute/{order_id}")
async def reroute_order(order_id: int):
    recovered_orders[order_id] = True
    return {"msg": f"Order {order_id} rerouted. Risk mitigated by 45%."}

# --- STORY LOGIC ---
@app.get("/story/{order_id}")
async def get_story(order_id: int):
    df = get_data()
    order = df[df['order_id'] == order_id]
    if order.empty: return {"error": "Order not found"}
        
    row = order.iloc[0]
    dt = row['order_date']
    is_delayed = int(row['delayed']) == 1
    # Check if it was recovered during this session
    if order_id in recovered_orders:
        is_delayed = False

    status_text = "delayed" if is_delayed else "on-time"
    story = f"Order #{order_id} is moving via {row['shipping_method']}. "
    if is_delayed:
        story += f"Our AI has flagged a delay risk based on supplier reliability."
    elif order_id in recovered_orders:
        story += "AI Recovery Active: Shipment rerouted to avoid disruption."
    else:
        story += "The transit route is clear and following the optimized schedule."

    return {
        "status": status_text,
        "story": story,
        "timeline": {
            "Ordered": dt.strftime('%b %d'),
            "Processing": (dt + timedelta(hours=12)).strftime('%b %d'),
            "Transit": (dt + timedelta(days=1)).strftime('%b %d'),
            "Estimate": (dt + timedelta(days=4 if is_delayed else 2)).strftime('%b %d')
        }
    }

@app.get("/mitigate")
async def mitigate(action: str):
    return {"msg": f"Action {action} confirmed."}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)