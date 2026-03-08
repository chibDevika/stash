import { useEffect, useRef, useState } from "react";
import { api } from "../api";

/**
 * Full-window drag-and-drop overlay for saving PDFs.
 * Listens on the window for drag events and shows an overlay when a file is dragged in.
 * On drop of a PDF, uploads it via api.uploadPdf and calls onSaved() on success.
 */
export default function PdfDropZone({ onSaved }) {
  const [visible, setVisible] = useState(false);
  const [isPdf, setIsPdf] = useState(true);
  const [status, setStatus] = useState(null); // null | 'uploading' | 'saved' | 'duplicate' | 'error'
  // Track drag enter/leave depth to avoid flickering when entering child elements
  const depth = useRef(0);

  useEffect(() => {
    function onDragEnter(e) {
      depth.current += 1;
      if (depth.current === 1) {
        // Check if any dragged item is a file; if we can see type info, validate PDF
        const items = Array.from(e.dataTransfer?.items || []);
        const fileItems = items.filter((i) => i.kind === "file");
        if (fileItems.length === 0) return; // not a file drag
        const allPdf = fileItems.every((i) => i.type === "application/pdf");
        setIsPdf(allPdf);
        setVisible(true);
        setStatus(null);
      }
    }

    function onDragOver(e) {
      e.preventDefault(); // required to allow drop
    }

    function onDragLeave() {
      depth.current -= 1;
      if (depth.current === 0) {
        setVisible(false);
      }
    }

    async function onDrop(e) {
      e.preventDefault();
      depth.current = 0;

      const file = e.dataTransfer?.files?.[0];
      if (!file) {
        setVisible(false);
        return;
      }

      if (file.type !== "application/pdf") {
        setIsPdf(false);
        // Show "PDFs only" briefly then dismiss
        setTimeout(() => setVisible(false), 1500);
        return;
      }

      setIsPdf(true);
      setStatus("uploading");

      try {
        await api.uploadPdf(file);
        setStatus("saved");
        onSaved?.();
        setTimeout(() => setVisible(false), 1200);
      } catch (err) {
        if (err.status === 409) {
          setStatus("duplicate");
        } else {
          setStatus("error");
        }
        setTimeout(() => setVisible(false), 2000);
      }
    }

    window.addEventListener("dragenter", onDragEnter);
    window.addEventListener("dragover", onDragOver);
    window.addEventListener("dragleave", onDragLeave);
    window.addEventListener("drop", onDrop);
    return () => {
      window.removeEventListener("dragenter", onDragEnter);
      window.removeEventListener("dragover", onDragOver);
      window.removeEventListener("dragleave", onDragLeave);
      window.removeEventListener("drop", onDrop);
    };
  }, [onSaved]);

  if (!visible) return null;

  let label = "Drop PDF to save it";
  let boxClass = "pdf-drop-box";
  if (!isPdf) {
    label = "PDFs only";
    boxClass += " invalid";
  } else if (status === "uploading") {
    label = "Saving…";
    boxClass += " pdf-uploading";
  } else if (status === "saved") {
    label = "Saved!";
  } else if (status === "duplicate") {
    label = "Already in your Stash";
  } else if (status === "error") {
    label = "Upload failed";
    boxClass += " invalid";
  }

  return (
    <div className="pdf-drop-overlay">
      <div className={boxClass}>
        <div className="pdf-drop-icon">📄</div>
        <div className="pdf-drop-label">{label}</div>
      </div>
    </div>
  );
}
