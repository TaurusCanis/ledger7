var paymentMethods = document.querySelectorAll(".payment-method");
var accountFormInput = document.querySelector("#id_account");
var creditCardFormInput = document.querySelector("#id_credit_card");

paymentMethods.forEach((item, i) => {
  item.addEventListener("click", function() {
    console.log(item.classList.contains("selected"))
    if (item.classList.contains("selected")) {
      classesToRemove = ["selected", "btn-success", "text-light"]
      item.classList.remove(...classesToRemove);
      accountFormInput.value = null
      creditCardFormInput.value = null
    }
    else {
      clearSelections();
      classesToAdd = ["selected", "btn-success", "text-light"]
      item.classList.add(...classesToAdd);
      if (item.classList.contains("pm-account")) {
        accountFormInput.value = item.id.split("_")[1]
      } else {
        creditCardFormInput.value = item.id.split("_")[1]
      }
    }
  });
});

function clearSelections() {
  accountFormInput.value = null
  creditCardFormInput.value = null

  paymentMethods.forEach((item, i) => {
    classesToRemove = ["selected", "btn-success", "text-light"]
    item.classList.remove(...classesToRemove);
  });
}
