const projectGrid = document.querySelector("#project-grid");

if (projectGrid && Array.isArray(window.portfolioProjects)) {
  window.portfolioProjects.forEach((project) => {
    const card = document.createElement("article");
    card.className = "project-card";

    const media = document.createElement("div");
    media.className = `project-media ${project.imageClass || ""}`;
    const image = document.createElement("img");
    image.src = project.image;
    image.alt = project.imageAlt || "";
    image.loading = project.number === "01" ? "eager" : "lazy";
    media.append(image);

    const info = document.createElement("div");
    info.className = "project-info";
    const meta = document.createElement("div");
    meta.className = "project-meta";
    const number = document.createElement("span");
    number.textContent = project.number;
    const category = document.createElement("span");
    category.textContent = project.category;
    meta.append(number, category);

    const title = document.createElement("h3");
    title.textContent = project.title;
    const description = document.createElement("p");
    description.textContent = project.description;
    info.append(meta, title, description);

    if (project.caseStudyUrl) {
      const link = document.createElement("a");
      link.className = "project-link";
      link.href = project.caseStudyUrl;
      link.setAttribute("aria-label", `View case study: ${project.title}`);
      link.append(media, info);
      card.append(link);
    } else {
      card.classList.add("project-card-preview");
      const status = document.createElement("span");
      status.className = "project-preview-note";
      status.setAttribute("role", "status");
      media.append(status);

      const trigger = document.createElement("button");
      trigger.className = "project-preview-trigger";
      trigger.type = "button";
      trigger.setAttribute("aria-label", `Show case study status: ${project.title}`);
      trigger.addEventListener("click", () => {
        status.textContent = project.previewMessage || "Case study coming soon.";
      });
      card.append(media, info, trigger);
    }
    projectGrid.append(card);
  });
}
