import React, { useState } from "react";
import DynamicContentForm from "./dynamic/DynamicContentForm";
import { DynamicContentProvider } from "./dynamic/DynamicContentProvider";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import axios from "axios";

const Pdf_filler = () => {
  const [htmlContent, setHtmlContent] = useState("");
  const [inputs, setInputs] = useState([]);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:5000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setHtmlContent(response.data.htmlContent); // Use the HTML content directly
      extractInputs(response.data.htmlContent); // Extract input fields from HTML
    } catch (error) {
      console.error("Error uploading file:", error);
    }
  };

  const extractInputs = (html) => {
    const regex = /\[([^\]]+)\]/g;
    let match;
    const newInputs = [];

    while ((match = regex.exec(html)) !== null) {
      newInputs.push({ placeholder: match[1], id: `input-${newInputs.length}` });
    }

    setInputs(newInputs);
  };

  const handleInputChange = (id, value) => {
    const input = inputs.find(input => input.id === id);
    if (!input) return;

    // Escape the placeholder for use in RegExp
    const escapedPlaceholder = input.placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`\\[${escapedPlaceholder}\\]`, 'g');

    // Replace all occurrences of the placeholder
    const newHtmlContent = htmlContent.replace(regex, value);
    setHtmlContent(newHtmlContent);
  };

  const handleDownloadPDF = () => {
    const content = document.getElementById("dynamic-content");
    html2canvas(content).then((canvas) => {
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "pt", "a4");
      const imgProps = pdf.getImageProperties(imgData);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save("draftai.pdf");
    });
  };

  return (
    <DynamicContentProvider initialContent={htmlContent}>
      <div className="h-full w-full text-lg text-black flex">
        <div className="w-3/4 bg-orange-100">
          <div
            className="w-11/12 h-full relative rounded p-10 mx-auto bg-white overflow-y-scroll"
            id="dynamic-content"
            dangerouslySetInnerHTML={{ __html: htmlContent }} // Set the HTML content
          />
        </div>
        <div className="text-black w-1/4 p-5 flex flex-col bg-white shadow-2xl overflow-y-scroll">
          <input type="file" onChange={handleFileUpload} className="mb-4" />
          <DynamicContentForm />
          {inputs.map(input => (
            <input
              key={input.id}
              type="text"
              placeholder={input.placeholder}
              onChange={(e) => handleInputChange(input.id, e.target.value)}
              className="mb-4 p-2 border border-gray-300 rounded"
            />
          ))}
          <button
            onClick={handleDownloadPDF}
            className="mt-4 p-2 bg-blue-500 text-white rounded"
          >
            Download as PDF
          </button>
        </div>
      </div>
    </DynamicContentProvider>
  );
};

export default Pdf_filler;
