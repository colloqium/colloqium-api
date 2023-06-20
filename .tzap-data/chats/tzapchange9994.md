

---
@role:assistant
Got it. To make the URL relative to the local application, you can use `window.location.origin` to get the origin of the current page, and append it to the front of the URL. Here is the modified code:

```javascript
function sendInteraction(button) {
  var interactionId = button.getAttribute("data-interaction-id");
  var interactionType = button.getAttribute("data-interaction-type");
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
```

This should append the base URL of the local application (e.g. `localhost:5000`) to the URL constructed from the `interactionId` and `interactionType` attributes of the button.
---
@role:user
The URL needs to be relative to the local application. E.g. if I'm at localhost.com this url should be localhost.com/interaction_type/interaction_id. This is returning just the "/interaction_type/interaction_id" part
---
@role:assistant
Sure, here is the modified code:

```javascript
function sendInteraction(button) {
  var interactionId = button.getAttribute("data-interaction-id");
  var interactionType = button.getAttribute("data-interaction-type");
  var url = interactionType + '/' + interactionId;
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
```

This code will extract the `interactionId` and `interactionType` from the button attributes and use them to construct the URL in the format you specified.
---
@role:user
Can you modify the interactions.js file so that it constructs the url from this button:nteraction-id={{ interaction.id }} data-interaction-type={{ interaction.interaction_type }}>Send</button>. The url format should be interaction_type/interaction_id
