 function makePdf(){
     let title = document.title + '_wsor.pdf';
     title = title.replace(' ', '_');
     title = title.toLowerCase();
     let wsor = document.getElementById('wsor');               
     let opt = {
       margin: 0.2,
       filename: title,
       jsPDF: { unit: 'in', format: 'letter', orientation: 'landscape' }
     };
     html2pdf().set(opt).from(wsor).save();
 }