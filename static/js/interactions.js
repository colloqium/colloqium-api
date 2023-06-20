function sendInteraction(button) {
    var interactionId = button.getAttribute("data-interaction-id");
    console.log("Interaction ID: " + interactionId);
    var interactionType = button.getAttribute("data-interaction-type");
    console.log("Interaction Type: " + interactionType);

    var url = window.location.origin + '/' + interactionType + '/' + interactionId;
    console.log(url);
  
    // Update interaction status
    fetch(url, { 
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ interaction_status: "InteractionStatus.HUMAN_CONFIRMED" })
    })
    .then(function(response) {
      if (response.status != 200) {
        button.innerText = "Error";
      } else {
        button.innerText = "Sent";
      }
      button.disabled = true;
    })
    .catch(function(error) {
      button.innerText = "Error";
      button.disabled = true;
    });
  }