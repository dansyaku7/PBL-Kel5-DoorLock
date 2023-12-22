// Change this to match your ESP8266 server IP address
const serverIP = "192.168.215.54";

function executeCodeA() {
  fetch(`http://${serverIP}/eksekusi-kode-A`)
    .then(response => response.json())
    .then(data => {
      console.log(data.status);
    })
    .catch(error => {
      console.error('Error:', error);
    });
}

function executeCodeB() {
  fetch(`http://${serverIP}/eksekusi-kode-B`)
    .then(response => response.json())
    .then(data => {
      console.log(data.status);
    })
    .catch(error => {
      console.error('Error:', error);
    });
}
