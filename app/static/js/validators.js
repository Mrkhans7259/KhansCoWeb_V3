document.addEventListener("input", function (event) {
    const input = event.target;
    const rule = input.dataset.validate;

    if (!rule) return;

    let value = input.value || "";

    if (rule === "mobile") {
        input.value = value.replace(/[^0-9]/g, "").slice(0, 10);
    }

    if (rule === "pincode") {
        input.value = value.replace(/[^0-9]/g, "").slice(0, 6);
    }

    if (rule === "aadhaar") {
        input.value = value.replace(/[^0-9]/g, "").slice(0, 12);
    }

    if (rule === "pan") {
        value = value.toUpperCase().replace(/[^A-Z0-9]/g, "");

        let part1 = value.slice(0, 5).replace(/[^A-Z]/g, "");
        let part2 = value.slice(5, 9).replace(/[^0-9]/g, "");
        let part3 = value.slice(9, 10).replace(/[^A-Z]/g, "");

        input.value = (part1 + part2 + part3).slice(0, 10);
    }

    if (rule === "gstin") {
        value = value.toUpperCase().replace(/[^A-Z0-9]/g, "");

        let p1 = value.slice(0, 2).replace(/[^0-9]/g, "");
        let p2 = value.slice(2, 7).replace(/[^A-Z]/g, "");
        let p3 = value.slice(7, 11).replace(/[^0-9]/g, "");
        let p4 = value.slice(11, 12).replace(/[^A-Z]/g, "");
        let p5 = value.slice(12, 15).replace(/[^A-Z0-9]/g, "");

        input.value = (p1 + p2 + p3 + p4 + p5).slice(0, 15);
    }

    if (rule === "name") {
        input.value = value.replace(/[^A-Za-z .&]/g, "");
    }

    if (rule === "business") {
        input.value = value.replace(/[^A-Za-z0-9 .,&()/-]/g, "");
    }
});
