function displayDateTime() {
    const dateTimeElement = document.getElementById("datetime");
    const now = new Date();
    const optionsTime = {
        hour: 'numeric',
        minute: 'numeric',
        hour12: false // Use 24-hour format
    };
    const timeString = now.toLocaleTimeString('pt-BR', optionsTime);

    const optionsDate = {
        month: 'long',
        day: 'numeric'
    };
    const dateString = now.toLocaleDateString('pt-BR', optionsDate);

    const finalDateTimeString = `
    <span class="bold">${timeString}</span><br>
    <span class="date">${dateString}</span>
`;
    dateTimeElement.innerHTML = finalDateTimeString;
}

setInterval(displayDateTime, 1000);
displayDateTime();
