fetch("/get_api_url")
    .then(response => response.json())
    .then(data => {
        const API_BASE = data.api_url;
    });

document.addEventListener("DOMContentLoaded", function () {
    loadUsers();

    document.getElementById("addUserButton").addEventListener("click", function () {
        document.getElementById("addUserPopup").style.display = "block";
    });

    document.getElementById("submitUser").addEventListener("click", function () {
        const userData = {
            admission_number: document.getElementById("admission_number").value,
            name: document.getElementById("name").value,
            place: document.getElementById("place").value,
            branch: document.getElementById("branch").value,
            semester: document.getElementById("semester").value,
            fixed_fare: parseInt(document.getElementById("fixed_fare").value)
        };

        fetch(`${API_BASE}/add_user`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(userData)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadUsers();
            document.getElementById("addUserPopup").style.display = "none";
        })
        .catch(error => console.error("Error adding user:", error));
    });
});

function loadUsers() {
    fetch(`${API_BASE}/get_users`)
        .then(response => response.json())
        .then(users => {
            const tableBody = document.querySelector("#userTable tbody");
            tableBody.innerHTML = "";

            users.forEach(user => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td><img src="${API_BASE}/qrcodes/${user.admission_number}.png" alt="QR Code" width="50"></td>
                    <td>${user.name}</td>
                    <td>${user.place}</td>
                    <td>${user.branch}</td>
                    <td>${user.semester}</td>
                    <td>₹${user.fixed_fare}</td>
                    <td>₹${user.total_fare}</td>
                    <td><button onclick="resetFare('${user.admission_number}')">Paid</button></td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error("Error loading users:", error));
}

function resetFare(admissionNumber) {
    fetch(`${API_BASE}/reset_fare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admission_number: admissionNumber })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadUsers();
    })
    .catch(error => console.error("Error resetting fare:", error));
}
