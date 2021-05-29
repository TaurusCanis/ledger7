var paymentMethods = document.querySelectorAll(".payment-method");
var creditCards = document.querySelectorAll(".credit-card");
var accountFormInput = document.querySelector("#id_account");
var creditCardFormInput = document.querySelector("#id_credit_card");

console.log("credit cards: ", creditCards)

creditCards.forEach((item, i) => {
  item.addEventListener("click", function() {
    if (item.classList.contains("selected")) {
      classesToRemove = ["selected", "btn-success", "text-light"]
      item.classList.remove(...classesToRemove);
      creditCardFormInput.value = null
    } else {
      clearCCSelections();
      classesToAdd = ["selected", "btn-success", "text-light"]
      item.classList.add(...classesToAdd);
      console.log("ITEM: ", item)
      if (item.classList.contains("credit-card")) {
        creditCardFormInput.value = item.id.split("_")[1]
      }
    }
  });
});


paymentMethods.forEach((item, i) => {
  item.addEventListener("click", function() {
    if (item.classList.contains("selected")) {
      classesToRemove = ["selected", "btn-success", "text-light"]
      item.classList.remove(...classesToRemove);
      accountFormInput.value = null
    }
    else {
      clearAccountSelections();
      classesToAdd = ["selected", "btn-success", "text-light"]
      item.classList.add(...classesToAdd);
      if (item.classList.contains("pm-account")) {
        accountFormInput.value = item.id.split("_")[1]
      }
    }
  });
});

function clearCCSelections() {
  creditCardFormInput.value = null
  creditCards.forEach((item, i) => {
    classesToRemove = ["selected", "btn-success", "text-light"]
    item.classList.remove(...classesToRemove);
  });
}

function clearAccountSelections() {
  accountFormInput.value = null
  paymentMethods.forEach((item, i) => {
    classesToRemove = ["selected", "btn-success", "text-light"]
    item.classList.remove(...classesToRemove);
  });
}
