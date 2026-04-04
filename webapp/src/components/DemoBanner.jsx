import React from "react";

export default function DemoBanner() {
  return (
    <div className="demo-banner">
      You're viewing a demo.{" "}
      <a
        href="https://github.com/chibDevika/stash"
        target="_blank"
        rel="noopener noreferrer"
        className="demo-banner-link"
      >
        Deploy your own Stash →
      </a>
    </div>
  );
}
