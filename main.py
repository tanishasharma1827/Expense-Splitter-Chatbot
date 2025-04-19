import streamlit as st
import re
from datetime import datetime
import pandas as pd
import random

# Set page configuration and custom CSS
st.set_page_config(page_title="Expense Splitter", page_icon="💰", layout="wide")

# Custom CSS for styling
def load_css():
    st.markdown("""
    <style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
        padding: 10px;
    }
    
    /* Header styling */
    h1 {
        color: #4b6584;
        text-align: center;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #20bf6b;
    }
    
    h2, h3 {
        color: #4b6584;
        margin-top: 1rem;
    }
    
    /* Card styling for different sections */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #20bf6b;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        background-color: #0ea55a;
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        border-radius: 5px;
        border: 1px solid #dfe4ea;
    }
    
    /* Transaction cards */
    .transaction-card {
        background-color: #f1f2f6;
        border-left: 4px solid #20bf6b;
        padding: 10px 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .transaction-amount {
        font-weight: bold;
        color: #20bf6b;
    }
    
    .transaction-details {
        display: flex;
        align-items: center;
    }
    
    .transaction-icon {
        margin-right: 10px;
    }
    
    /* Response area */
    .response-area {
        background-color: #e3f9ee;
        border-left: 4px solid #20bf6b;
        padding: 15px;
        border-radius: 5px;
        margin-top: 15px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f1f2f6;
        border-radius: 5px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #dfe4ea;
        color: #a5b1c2;
        font-size: 0.8rem;
    }
    
    /* Examples list */
    .examples-list {
        margin-top: 1rem;
    }
    
    .examples-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .example-item {
        background-color: #f1f2f6;
        padding: 8px 12px;
        margin-bottom: 8px;
        border-radius: 5px;
        cursor: pointer;
    }
    
    .example-item:hover {
        background-color: #e3f9ee;
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 40px 20px;
    }
    
    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        color: #a5b1c2;
    }
    
    .empty-state-text {
        color: #576574;
    }
    
    /* Card headers */
    .card-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .card-header-icon {
        margin-right: 0.5rem;
        color: #4b6584;
        font-size: 1.2rem;
    }
    
    .card-title {
        margin: 0;
        font-size: 1.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

class ExpenseSplitter:
    def __init__(self):  # Fixed the init method with double underscores
        # Initialize or load existing expenses
        if 'expenses' not in st.session_state:
            st.session_state.expenses = []
        if 'people' not in st.session_state:
            st.session_state.people = set()
        if 'expense_colors' not in st.session_state:
            st.session_state.expense_colors = {}
        
    def add_expense(self, paid_by, amount, description, split_among=None, date=None):
        # Generate a color for the expense
        color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if split_among is None:
            split_among = list(st.session_state.people)
        else:
            # Add all people to the global set
            for person in split_among:
                st.session_state.people.add(person)
        
        # Add payer to the global set of people
        st.session_state.people.add(paid_by)
        
        # Calculate the amount per person
        amount_per_person = amount / len(split_among)
        
        # Add the expense to the list with color
        st.session_state.expenses.append({
            "date": date,
            "paid_by": paid_by,
            "amount": amount,
            "description": description,
            "split_among": split_among,
            "amount_per_person": amount_per_person,
            "color": color  # Added color field
        })
        
        return f"Added expense: {description} - ${amount:.2f} paid by {paid_by}, split among {', '.join(split_among)}."
    
    def calculate_balances(self):
        # Initialize balance dict
        balances = {person: 0 for person in st.session_state.people}
        
        # Calculate what each person has paid and owes
        for expense in st.session_state.expenses:
            paid_by = expense["paid_by"]
            amount = expense["amount"]
            split_among = expense["split_among"]
            amount_per_person = expense["amount_per_person"]
            
            # Add amount to the balance of the person who paid
            balances[paid_by] += amount
            
            # Subtract amount from the balance of each person who shares the expense
            for person in split_among:
                balances[person] -= amount_per_person
        
        return balances
    
    def get_transactions(self):
        balances = self.calculate_balances()
        
        # Separate debtors and creditors
        debtors = {person: balance for person, balance in balances.items() if balance < 0}
        creditors = {person: balance for person, balance in balances.items() if balance > 0}
        
        transactions = []
        
        # Create transaction list
        for debtor, debt in sorted(debtors.items(), key=lambda x: x[1]):
            debt = abs(debt)  # Make the debt positive for calculations
            for creditor, credit in sorted(creditors.items(), key=lambda x: x[1], reverse=True):
                if debt <= 0 or credit <= 0:
                    continue
                    
                amount = min(debt, credit)
                transactions.append({
                    "from": debtor,
                    "to": creditor,
                    "amount": amount
                })
                
                # Update remaining balances
                debt -= amount
                creditors[creditor] -= amount
                
        return transactions
    
    def parse_command(self, command):
        # Convert command to lowercase
        command = command.lower()
        
        # Check for expense command patterns
        expense_pattern = r'(?P<paid_by>\w+)\s+paid\s+(?P<amount>\d+(\.\d+)?)\s+for\s+(?P<description>.+?)((\s+split\s+(?:between|among|with)\s+(?P<split_among>.+?))?(\s+on\s+(?P<date>.+))?)?$'
        match = re.search(expense_pattern, command)
        
        if match:
            paid_by = match.group('paid_by').strip()
            amount = float(match.group('amount'))
            description = match.group('description').strip()
            
            split_among_str = match.group('split_among')
            date_str = match.group('date')
            
            # Parse the people to split among
            split_among = None
            if split_among_str:
                split_among = [person.strip() for person in re.split(r',\s*|(?:\s+and\s+)', split_among_str)]
                # Include the payer if they're not already in the list
                if paid_by not in split_among:
                    split_among.append(paid_by)
            
            # Parse the date if provided
            date = None
            if date_str:
                try:
                    date = datetime.strptime(date_str.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
                except ValueError:
                    date = datetime.now().strftime("%Y-%m-%d")
            
            return self.add_expense(paid_by, amount, description, split_among, date)
        
        # Check for balance command
        if "balance" in command or "who owes" in command or "owes who" in command:
            balances = self.calculate_balances()
            transactions = self.get_transactions()
            
            if not transactions:
                return "All settled up! No one owes anything."
            
            result = "Here's who owes whom:\n"
            for t in transactions:
                result += f"{t['from']} owes {t['to']} ${t['amount']:.2f}\n"
            
            return result
        
        # Check for summary command
        if "summary" in command or "list expenses" in command:
            if not st.session_state.expenses:
                return "No expenses recorded yet."
            
            result = "Expense Summary:\n"
            for idx, expense in enumerate(st.session_state.expenses):
                result += f"{idx+1}. {expense['description']} - ${expense['amount']:.2f} paid by {expense['paid_by']}, " \
                         f"split among {', '.join(expense['split_among'])}\n"
            
            return result
        
        # Check for help command
        if "help" in command:
            return """
            I understand these commands:
            - "[name] paid [amount] for [description] split among/between/with [person1, person2, ...]"
            - "balance" or "who owes" to see who owes whom
            - "summary" or "list expenses" to see all recorded expenses
            - "help" to see this message
            - "clear" to reset all expenses
            """
        
        # Check for clear command
        if "clear" in command or "reset" in command:
            st.session_state.expenses = []
            st.session_state.people = set()
            return "All expenses have been cleared."
        
        return "I didn't understand that command. Type 'help' to see what I can do."

# Streamlit app
def main():
    # Load custom CSS
    load_css()
    
    # App header
    st.markdown("<h1>💰 Split Expenses with Ease</h1>", unsafe_allow_html=True)
    
    # Initialize session state variables if they don't exist
    if 'expenses' not in st.session_state:
        st.session_state.expenses = []
    if 'people' not in st.session_state:
        st.session_state.people = set()
    if 'expense_colors' not in st.session_state:
        st.session_state.expense_colors = {}
    
    # Initialize the splitter
    splitter = ExpenseSplitter()
    
    # Two-column layout with adjusted ratio
    col1, col2 = st.columns([5, 4])
    
    with col1:
        # Input section
        st.markdown("<div class='card animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card-header">
            <div class="card-header-icon">📝</div>
            <h2 class="card-title">Add Expense or Command</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat input area with examples
        user_input = st.text_input(
            "",
            placeholder="e.g. 'John paid 50 for dinner split among John, Mary, Bob'",
            key="user_input"
        )
        
        # Submit and clear buttons in same row
        col_submit, col_clear = st.columns([1, 1])
        with col_submit:
            submit_button = st.button("Submit Command", key="submit")
        with col_clear:
            st.markdown("<div class='button-secondary'>", unsafe_allow_html=True)
            clear_input = st.button("Clear Input", key="clear_input")
            st.markdown("</div>", unsafe_allow_html=True)

        if submit_button and user_input:
            response = splitter.parse_command(user_input)
            st.session_state.last_response = response
            st.session_state.show_response = True
        
        if clear_input:
            st.session_state.user_input = ""
            
        # Show example commands
        st.markdown("""
        <div class="examples-list">
            <div class="examples-title">📝 Example commands (click to use):</div>
        """, unsafe_allow_html=True)
        
        example_commands = [
            "John paid 50 for dinner split among John, Mary, Bob",
            "Sarah paid 30 for movie tickets split between Sarah and Mike",
            "Alex paid 75 for groceries split with Taylor",
            "balance",
            "summary",
            "help",
            "clear"
        ]
        
        for cmd in example_commands:
            st.markdown(f"""
            <div class="example-item" onclick="
                document.querySelector('.stTextInput input').value = '{cmd}';
                document.querySelector('.stTextInput input').dispatchEvent(new Event('input', {{ bubbles: true }}));
            ">
                {cmd}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display response if available
        if 'show_response' in st.session_state and st.session_state.show_response:
            st.markdown("<div class='response-area animate-fade-in'>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="response-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 11.5C21.0034 12.8199 20.6951 14.1219 20.1 15.3C19.3944 16.7118 18.3098 17.8992 16.9674 18.7293C15.6251 19.5594 14.0782 19.9994 12.5 20C11.1801 20.0035 9.87812 19.6951 8.7 19.1L3 21L4.9 15.3C4.30493 14.1219 3.99656 12.8199 4 11.5C4.00061 9.92179 4.44061 8.37488 5.27072 7.03258C6.10083 5.69028 7.28825 4.6056 8.7 3.90003C9.87812 3.30496 11.1801 2.99659 12.5 3.00003H13C15.0843 3.11502 17.053 3.99479 18.5291 5.47089C20.0052 6.94699 20.885 8.91568 21 11V11.5Z" stroke="#4361ee" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Response
            </div>
            {st.session_state.last_response}
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='button-secondary' style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
            if st.button("Clear Response", key="clear_response"):
                st.session_state.show_response = False
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Display expense history
        if st.session_state.expenses:
            st.markdown("<div class='card animate-fade-in'>", unsafe_allow_html=True)
            st.markdown("""
            <div class="card-header">
                <div class="card-header-icon">📋</div>
                <h2 class="card-title">Expense History</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a DataFrame for expense history instead of HTML
            expense_data = []
            for expense in st.session_state.expenses:
                expense_data.append({
                    "Date": expense["date"],
                    "Description": expense["description"],
                    "Amount": f"${expense['amount']:.2f}",
                    "Paid By": expense["paid_by"],
                    "Split Among": ", ".join(expense["split_among"])
                })
            
            # Display as Streamlit table
            if expense_data:
                expense_df = pd.DataFrame(expense_data)
                st.dataframe(expense_df, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Balances and Transactions Section
        if st.session_state.expenses:
            # Current Balances
            st.markdown("<div class='card animate-fade-in'>", unsafe_allow_html=True)
            st.markdown("""
            <div class="card-header">
                <div class="card-header-icon">💵</div>
                <h2 class="card-title">Current Balances</h2>
            </div>
            """, unsafe_allow_html=True)
            
            balances = splitter.calculate_balances()
            
            # Create a DataFrame for balances instead of HTML string
            balance_data = []
            for person, balance in balances.items():
                status_text = "Settled" if abs(balance) < 0.01 else "Is Owed" if balance > 0 else "Owes"
                balance_data.append({
                    "Person": person,
                    "Balance": f"${balance:.2f}",
                    "Status": status_text
                })
            
            # Display as Streamlit table
            if balance_data:
                balance_df = pd.DataFrame(balance_data)
                st.table(balance_df)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Suggested Transactions
            st.markdown("<div class='card animate-fade-in'>", unsafe_allow_html=True)
            st.markdown("""
            <div class="card-header">
                <div class="card-header-icon">💸</div>
                <h2 class="card-title">Suggested Transactions</h2>
            </div>
            """, unsafe_allow_html=True)
            
            transactions = splitter.get_transactions()
            
            if transactions:
                for t in transactions:
                    st.markdown(f"""
                    <div class='transaction-card'>
                        <div class="transaction-details">
                            <div class="transaction-icon">↗️</div>
                            <span class="transaction-text"><b>{t['from']}</b> owes <b>{t['to']}</b></span>
                        </div>
                        <div class="transaction-amount">${t['amount']:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">✅</div>
                    <div style="color: var(--accent); font-weight: 600;">All settled up! No one owes anything.</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Clear data button
            st.markdown("<div class='button-danger' style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
            if st.button("Reset All Expenses", key="reset_all"):
                st.session_state.expenses = []
                st.session_state.people = set()
                st.session_state.expense_colors = {}
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Empty state when no expenses
            st.markdown("<div class='card empty-state animate-fade-in'>", unsafe_allow_html=True)
            st.markdown("""
            <div class="empty-state-icon">📊</div>
            <div class="empty-state-text">No expenses recorded yet. Add your first expense to get started!</div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("<div class='footer'>Expense Splitter App • Made with Streamlit</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()