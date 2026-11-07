/*!
 * \file
 * \brief Class pyaf::module::Monitor_BFER_AR: BFER monitor whose clones share their counters (pyaff3ct only).
 *
 * In a multi-threaded `streampu.Sequence`, each thread runs a clone of the modules. With `Monitor_BFER`, each clone
 * counts its own errors and the sequence stops as soon as one of them reaches `max_fe` (the reduced FER is then
 * biased upwards); the AFF3CT simulator avoids this with a `Monitor_reduction` that the Python interface does not
 * have. `Monitor_BFER_AR` ("atomic reduction", after the class of the same name of py_aff3ct) shares the counters
 * between the monitor and its clones:
 *
 * - each checked frame is added to the shared totals (under a mutex), then the totals are copied into the clone and
 *   into the monitor it comes from (the "root", that the user keeps): every `get_n_fe()`, `get_fer()`... and
 *   `is_done()` (which first refreshes the counters from the totals) see the totals, so all the threads stop when
 *   the totals reach `max_fe`, and the reporters (Reporter_BFER, Reporter_throughput) can be given the root as is;
 * - `reset()` (root or clone) resets the totals: resetting the root between two SNR points is enough.
 *
 * It is a `Monitor_BFER<B>`: the counters are the ones of the base class, only their update changes. To be removed
 * when AFF3CT / pystreampu offer an equivalent.
 */
#ifndef PYAF_MODULE_MONITOR_BFER_AR_MONITOR_BFER_AR_HPP_
#define PYAF_MODULE_MONITOR_BFER_AR_MONITOR_BFER_AR_HPP_

#include <memory>
#include <mutex>
#include <string>

#include "Module/Monitor/BFER/Monitor_BFER.hpp"

namespace pyaf
{
namespace module
{
template<typename B = int>
class Monitor_BFER_AR : public aff3ct::module::Monitor_BFER<B>
{
  protected:
    using Base = aff3ct::module::Monitor_BFER<B>;
    using Attributes = typename Base::Attributes;

    struct Shared
    {
        std::mutex mtx;
        unsigned long long n_fra = 0;
        unsigned long long n_be = 0;
        unsigned long long n_fe = 0;
        Monitor_BFER_AR<B>* root = nullptr; // the monitor built by the user (nullptr once destroyed)
    };

    std::shared_ptr<Shared> shared;

  public:
    Monitor_BFER_AR(const int K,
                    const unsigned max_fe,
                    const unsigned max_n_frames = 0,
                    const bool count_unknown_values = false)
      : Base(K, max_fe, max_n_frames, count_unknown_values)
      , shared(std::make_shared<Shared>())
    {
        this->set_name("Monitor_BFER_AR");
        shared->root = this;
    }

    // the clones share `shared` (copy of the shared_ptr), the root stays the original monitor
    Monitor_BFER_AR(const Monitor_BFER_AR<B>&) = default;

    virtual ~Monitor_BFER_AR()
    {
        std::lock_guard<std::mutex> lock(shared->mtx);
        if (shared->root == this) shared->root = nullptr;
    }

    virtual Monitor_BFER_AR<B>* clone() const
    {
        // same checks as Monitor_BFER (throws if callbacks are recorded); a named object: `std::unique_ptr<Base>(...);`
        // alone is parsed as a declaration by clang
        const std::unique_ptr<Base> checked(Base::clone());
        auto m = new Monitor_BFER_AR<B>(*this);
        m->deep_copy(*this);
        return m;
    }

    //! True if `m` shares its counters with this monitor (clone, or monitor cloned from).
    bool is_shared_with(const Monitor_BFER_AR<B>& m) const { return this->shared == m.shared; }

    //! Refreshes the counters from the totals (another clone may have counted, or reset them), then as Monitor_BFER.
    virtual bool is_done() const
    {
        auto self = const_cast<Monitor_BFER_AR<B>*>(this);
        {
            std::lock_guard<std::mutex> lock(shared->mtx);
            self->Base::copy(totals());
        }
        return Base::is_done();
    }

    virtual void reset()
    {
        Base::reset();
        std::lock_guard<std::mutex> lock(shared->mtx);
        shared->n_fra = shared->n_be = shared->n_fe = 0;
        if (shared->root != nullptr && shared->root != this) shared->root->Base::copy(Attributes());
    }

  protected:
    Attributes totals() const // shared->mtx must be held
    {
        Attributes a;
        a.n_fra = shared->n_fra;
        a.n_be = shared->n_be;
        a.n_fe = shared->n_fe;
        return a;
    }

    virtual int __check_errors(const B* U, const B* V, const size_t frame_id)
    {
        // local count (histogram, callbacks), then into the totals, that replace the local counters
        const int n_be = Base::__check_errors(U, V, frame_id);
        Attributes a;
        {
            std::lock_guard<std::mutex> lock(shared->mtx);
            shared->n_fra += 1;
            shared->n_be += (unsigned long long)n_be;
            shared->n_fe += n_be ? 1 : 0;
            a = totals();
            if (shared->root != nullptr && shared->root != this) shared->root->Base::copy(a);
        }
        Base::copy(a);
        return n_be;
    }
};
} // namespace module
} // namespace pyaf

#endif // PYAF_MODULE_MONITOR_BFER_AR_MONITOR_BFER_AR_HPP_
