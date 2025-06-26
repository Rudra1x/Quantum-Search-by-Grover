import streamlit as st
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import random
import io

# Simulate 1024 friends with random phone numbers
friends = {
    f"Friend_{i}": (i, ''.join(random.choices("0123456789", k=10)))
    for i in range(1024)
}

# App UI Setup
st.set_page_config(page_title="Grover's Search Demo", layout="centered")
st.title("🔍 Quantum Friend Finder with Grover's Algorithm")
st.markdown("Use **Grover's Quantum Search** to find your friend's phone number among 1024 possibilities!")

# User selects a friend to search
target_name = st.selectbox("Select a friend to search:", list(friends.keys()))
search = st.button("🔎 Run Grover's Algorithm")

# Define the Oracle
def apply_oracle(qc, target_bin):
    # Flip qubits where target bit is 0
    for i, bit in enumerate(reversed(target_bin)):
        if bit == '0':
            qc.x(i)
    # Multi-controlled-Z via H + mcx + H
    qc.h(9)
    qc.mcx(list(range(9)), 9)
    qc.h(9)
    # Uncompute the flips
    for i, bit in enumerate(reversed(target_bin)):
        if bit == '0':
            qc.x(i)

# Define the Diffuser (Inversion about average)
def apply_diffuser(qc):
    qc.h(range(10))
    qc.x(range(10))
    qc.h(9)
    qc.mcx(list(range(9)), 9)
    qc.h(9)
    qc.x(range(10))
    qc.h(range(10))

# Run Grover's Algorithm when button is pressed
if search:
    st.success(f"🔎 Searching for `{target_name}`...")

    # Get index and convert to 10-bit binary
    target_index = friends[target_name][0]
    target_bin = format(target_index, '010b')

    # Initialize 10-qubit quantum circuit
    qc = QuantumCircuit(10, 10)
    qc.h(range(10))  # Start in superposition

    # Apply Grover iterations (reduced to 6 for performance)
    for _ in range(6):
        apply_oracle(qc, target_bin)
        apply_diffuser(qc)

    # Measure all qubits
    qc.measure(range(10), range(10))

    # Run the simulation
    backend = Aer.get_backend("qasm_simulator")
    compiled = transpile(qc, backend)
    job = backend.run(compiled, shots=1024)
    result = job.result()
    counts = result.get_counts()

    # Show top 10 measurement results
    st.subheader(" Top 10 Most Probable States")
    top_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10])
    fig2 = plot_histogram(top_counts)
    st.pyplot(fig2)

    # Show state probabilities
    st.markdown("### 📈 Probability of Each State:")
    total_shots = sum(counts.values())
    for state, count in top_counts.items():
        prob = count / total_shots
        st.write(f" State `{state}` → **{prob:.4f}**")

    # Display Friend Info
    st.info(f" Friend: **{target_name}**")
    st.info(f" Phone Number: **{friends[target_name][1]}**")
    st.info(f" Target Binary Index: `{target_bin}`")

    # Show Circuit Diagram (neatly folded)
    st.subheader(" Quantum Circuit Diagram")
    # Safer draw method for Streamlit Cloud
    svg = qc.draw(output="mpl", fold=150)
    st.components.v1.html(svg, height=600, scrolling=True)


    # Download Buttons
    buf2 = io.BytesIO()
    fig2.savefig(buf2, format="png")
    st.download_button(" Download Top 10 Histogram", buf2.getvalue(), file_name="top10_histogram.png", mime="image/png")

    #buf3 = io.BytesIO()
    #fig3.figure.savefig(buf3, format="png")
    #st.download_button(" Download Circuit Diagram", buf3.getvalue(), file_name="circuit_diagram.png", mime="image/png")
