import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURATIE & MOCK DATA ---
st.set_page_config(page_title="Linkhub Tegoed POC", layout="wide")

def load_data():
    # Klanten met hun vaste maandelijkse budget
    customers = {
        "Klant A (Groot)": {"monthly_budget": 2000},
        "Klant B (Middel)": {"monthly_budget": 1000},
        "Klant C (Klein)": {"monthly_budget": 500}
    }

    # Gesimuleerde orders (links die 'Live' zijn gegaan)
    orders_data = [
        # Klant A: Jan (1500), Feb (2200), Maa (1800)
        {"customer": "Klant A (Groot)", "date": "2024-01-15", "cost": 1500},
        {"customer": "Klant A (Groot)", "date": "2024-02-10", "cost": 1200},
        {"customer": "Klant A (Groot)", "date": "2024-02-25", "cost": 1000},
        {"customer": "Klant A (Groot)", "date": "2024-03-05", "cost": 1800},
        
        # Klant B: Jan (1200 -> overspend), Feb (500)
        {"customer": "Klant B (Middel)", "date": "2024-01-20", "cost": 1200},
        {"customer": "Klant B (Middel)", "date": "2024-02-15", "cost": 500},
    ]
    
    df_orders = pd.DataFrame(orders_data)
    df_orders['date'] = pd.to_datetime(df_orders['date'])
    return customers, df_orders

# --- LOGICA: BEREKENING TEGOEDEN ---
def calculate_monthly_stats(customer_name, monthly_budget, df_orders):
    # Filter orders voor deze klant
    client_orders = df_orders[df_orders['customer'] == customer_name].copy()
    
    # Groepeer per maand
    client_orders['month'] = client_orders['date'].dt.to_period('M')
    monthly_spend = client_orders.groupby('month')['cost'].sum().reset_index()
    
    # We willen een overzicht van de laatste 6 maanden (ook als er geen orders waren)
    all_months = pd.period_range(start='2024-01', periods=4, freq='M')
    stats = []
    rollover = 0
    
    for month in all_months:
        spent = monthly_spend[monthly_spend['month'] == month]['cost'].sum()
        total_available = monthly_budget + rollover
        end_balance = total_available - spent
        
        stats.append({
            "Maand": str(month),
            "Startsaldo (Rollover)": round(rollover, 2),
            "Nieuw Budget": round(monthly_budget, 2),
            "Totaal Beschikbaar": round(total_available, 2),
            "Gerealiseerd (Spent)": round(spent, 2),
            "Eindsaldo (naar volgende mnd)": round(end_balance, 2)
        })
        
        # Het eindsaldo van deze maand is de rollover voor de volgende
        rollover = end_balance
        
    return pd.DataFrame(stats)

# --- STREAMLIT UI ---
def main():
    st.title("🔗 Linkhub Tegoed & Rollover POC")
    st.markdown("Dit dashboard laat zien hoe ongebruikt budget meegaat naar de volgende maand.")

    customers, df_orders = load_data()

    # Sidebar
    st.sidebar.header("Instellingen")
    selected_client = st.sidebar.selectbox("Selecteer een klant", list(customers.keys()))
    
    budget = customers[selected_client]["monthly_budget"]
    st.sidebar.info(f"Vast Maandbudget: €{budget}")

    # Berekening
    report_df = calculate_monthly_stats(selected_client, budget, df_orders)

    # Metrics bovenaan
    latest = report_df.iloc[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric("Huidig Eindsaldo", f"€{latest['Eindsaldo (naar volgende mnd)']}")
    col2.metric("Totaal Uitgegeven (Laatste mnd)", f"€{latest['Gerealiseerd (Spent)']}")
    col3.metric("Status", "Overspend" if latest['Eindsaldo (naar volgende mnd)'] < 0 else "Gezond")

    # Tabel tonen
    st.subheader(f"Maandoverzicht voor {selected_client}")
    st.table(report_df)

    # Grafiek van besteding vs budget
    st.subheader("Bestedingsverloop")
    chart_data = report_df.set_index("Maand")[["Gerealiseerd (Spent)", "Totaal Beschikbaar"]]
    st.line_chart(chart_data)

    # Ruwe data sectie
    with st.expander("Bekijk ruwe order data (Live Links)"):
        st.write(df_orders[df_orders['customer'] == selected_client])

if __name__ == "__main__":
    main()
