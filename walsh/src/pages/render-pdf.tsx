import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Document, Page } from "react-pdf";
import { Box } from "@mantine/core";

export const RenderPDF: React.FC = () => {
  const [queries] = useSearchParams();
  const pdfUrl = queries.get("pdf") || queries.get("url") || "";
  const frameId = queries.get("frameId") || "";
  const [numPages, setNumPages] = useState<number>(0);
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => {
      setWidth(window.innerWidth);
      // Post message to parent with new dimensions
      window.parent.postMessage(
        {
          type: "pdf-dimensions",
          width: window.innerWidth,
          height: document.body.scrollHeight,
          frameId,
        },
        "*"
      );
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [frameId]);

  const handleDocumentLoad = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    // Post initial dimensions after PDF loads
    setTimeout(() => {
      window.parent.postMessage(
        {
          type: "pdf-dimensions",
          width: window.innerWidth,
          height: document.body.scrollHeight,
          frameId,
        },
        "*"
      );
    }, 100);
  };

  return (
    <Box sx={{ overflow: "auto", width: "100%" }}>
      <Document file={{ url: pdfUrl }} onLoadSuccess={handleDocumentLoad}>
        {Array.from(new Array(numPages), (_el, index) => (
          <Page
            key={`page_${index + 1}`}
            pageNumber={index + 1}
            width={width}
            scale={0.8}
            renderTextLayer={true}
            renderAnnotationLayer={true}
          />
        ))}
      </Document>
    </Box>
  );
};
