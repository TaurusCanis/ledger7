var transferToAccounts = document.getElementsByName("account")
var transferFromAccounts = document.querySelectorAll("transfer_from_account")

// transferToAccounts.forEach((item, i) => {
//   console.log("A")
//   item.addEventListener("click", function() {
//     a = Array.prototype.slice.call(transferFromAccounts).filter(account => account.value == item.value && account.checked)
//     console.log("A.filter: ", a)
//     if (a) {
//       alert("MATCHES")
//     }
//   })
// });
//
// transferFromAccounts.forEach((item, i) => {
//   console.log("B")
//   item.addEventListener("click", function() {
//     b = Array.prototype.slice.call(transferToAccounts).filter(account => account.value == item.value && account.checked)
//     console.log("B.filter: ", b)
//     if (b) {
//       alert("MATCHES")
//     }
//   })
// });


/**
var transferToAccounts = document.querySelectorAll(".transfer-to-account");
var transferFromAccounts = document.querySelectorAll(".transfer-from-account");
var accountFormInput = document.querySelector("#id_account");
var transferToAccountFormInput = document.querySelector("#id_transfer_from_account");

console.log("accountFormInput: ", accountFormInput)
console.log("transferToAccountFormInput: ", transferToAccountFormInput)

transferToAccounts.forEach((item, i) => {
  item.addEventListener("click", function() {
    if (item.classList.contains("selected")) {
      classesToRemove = ["selected", "btn-success", "text-light"]
      item.classList.remove(...classesToRemove);
      transferToAccountFormInput.value = null
    } else {
      if (item.id.split("_")[1] == accountFormInput.value) {
        // transferToAccountFormInput.value = null
        alert("You must choose different accounts to transfer funds.")
      } else {
        clearCCSelections();
        classesToAdd = ["selected", "btn-success", "text-light"]
        item.classList.add(...classesToAdd);
        transferToAccountFormInput.value = item.id.split("_")[1]
      }
    }
  });
});

transferFromAccounts.forEach((item, i) => {
  item.addEventListener("click", function() {
    if (item.classList.contains("selected")) {
      classesToRemove = ["selected", "btn-success", "text-light"]
      item.classList.remove(...classesToRemove);
      accountFormInput.value = null
    } else {
      if (item.id.split("_")[1] == transferToAccountFormInput.value) {
        // accountFormInput.value = null
        alert("You must choose different accounts to transfer funds.")
      } else {
        clearAccountSelections();
        classesToAdd = ["selected", "btn-success", "text-light"]
        item.classList.add(...classesToAdd);
        accountFormInput.value = item.id.split("_")[1]
      }
    }
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
**/
