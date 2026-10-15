import { landingTestimonials } from "../content/landing-testimonials";
import { localizePublicTestimonials, type ApprovedPublicTestimonial } from "../lib/public-testimonials";

/** A static reading row avoids an unsolicited carousel and needs no motion controls. */
export function LandingTestimonials({
  he,
  entries = landingTestimonials,
  className,
}: {
  he: boolean;
  entries?: readonly ApprovedPublicTestimonial[];
  className?: string;
}) {
  const reviews = localizePublicTestimonials(entries, he ? "he" : "en");
  if (!reviews.length) return null;
  return (
    <section className={className} aria-labelledby="landing-testimonials-title">
      <h2 id="landing-testimonials-title">{he ? "מה אומרים מי שמתרגלים" : "From people practicing with JobRun"}</h2>
      <ul>
        {reviews.map(review => (
          <li key={review.id}>
            <figure>
              <blockquote dir="auto"><p>{review.quote}</p></blockquote>
              <figcaption>
                <strong dir="auto">{review.displayName}</strong>
                {review.context && <span dir="auto">{review.context}</span>}
              </figcaption>
            </figure>
          </li>
        ))}
      </ul>
    </section>
  );
}
