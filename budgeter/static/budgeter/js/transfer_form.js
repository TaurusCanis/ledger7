var transferToAccounts = document.querySelectorAll(".transfer-to-account");
var transferFromAccounts = document.querySelectorAll(".transfer-from-account");
var accountFormInput = document.querySelector("#id_account");
var transferToAccountFormInput = document.querySelector("#id_transfer_to_account");

console.log("accountFormInput: ", accountFormInput)

console.log("transferToAccounts: ", transferToAccounts)
console.log("transferFromAccounts: ", transferFromAccounts)

transferToAccounts.forEach((item, i) => {
  item.addEventListener("click", function() {
    console.log("transferToAccounts, item: ", item)
    if (item.classList.contains("selected")) {
      classesToRemove = ["selected", "btn-success", "text-light"]
      item.classList.remove(...classesToRemove);
      transferToAccountFormInput.value = null
    } else {
      if (item.id.split("_")[1] == accountFormInput.value) {
        console.log("SAME")
        // transferToAccountFormInput.value = null
        alert("You must choose different accounts to transfer funds.")
      } else {
        clearCCSelections();
        classesToAdd = ["selected", "btn-success", "text-light"]
        item.classList.add(...classesToAdd);
        transferToAccountFormInput.value = item.id.split("_")[1]
      }
    }
    console.log("item.id.split('_')[1]: ", transferToAccountFormInput.value)
    console.log("accountFormInput.value: ", accountFormInput.value)
  });
});

transferFromAccounts.forEach((item, i) => {
  item.addEventListener("click", function() {
    console.log("transferFromAccounts, item: ", item)
    if (item.classList.contains("selected")) {
      classesToRemove = ["selected", "btn-success", "text-light"]
      item.classList.remove(...classesToRemove);
      accountFormInput.value = null
    } else {
      if (item.id.split("_")[1] == transferToAccountFormInput.value) {
        console.log("SAME")
        // accountFormInput.value = null
        alert("You must choose different accounts to transfer funds.")
      } else {
        clearAccountSelections();
        classesToAdd = ["selected", "btn-success", "text-light"]
        item.classList.add(...classesToAdd);
        accountFormInput.value = item.id.split("_")[1]
      }
    }
    console.log("item.id.split('_')[1]: ", transferToAccountFormInput.value)
    console.log("accountFormInput.value: ", accountFormInput.value)
  });
});



// transferFromAccounts.forEach((item, i) => {
//   item.addEventListener("click", function() {
//     if (item.classList.contains("selected")) {
//       classesToRemove = ["selected", "btn-success", "text-light"]
//       item.classList.remove(...classesToRemove);
//       if (item.id.split("_")[1] == accountFormInput.value) {
//         accountFormInput.value = null
//       }
//     }
//     else {
//       clearAccountSelections();
//       classesToAdd = ["selected", "btn-success", "text-light"]
//       item.classList.add(...classesToAdd);
//       if (item.classList.contains("pm-account")) {
//         accountFormInput.value = item.id.split("_")[1]
//       }
//     }
//   });
// });

function clearCCSelections() {
  transferToAccountFormInput.value = null
  transferToAccounts.forEach((item, i) => {
    classesToRemove = ["selected", "btn-success", "text-light"]
    item.classList.remove(...classesToRemove);
  });
}

function clearAccountSelections() {
  accountFormInput.value = null
  transferFromAccounts.forEach((item, i) => {
    classesToRemove = ["selected", "btn-success", "text-light"]
    item.classList.remove(...classesToRemove);
  });
}
